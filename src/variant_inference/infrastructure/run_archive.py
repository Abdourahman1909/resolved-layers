from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from pathlib import Path

from variant_inference.application.verified_run import canonical_prediction_payload
from variant_inference.domain.models import (
    ArchivedRun,
    AuditEntry,
    Finding,
    LoadedVerifiedRun,
    PredictionRecord,
    RunArchiveEntry,
    SourceReferenceState,
    SourceReferenceStatus,
    TransformationAudit,
    VerifiedRun,
)


class RunArchiveError(RuntimeError):
    pass


class DirectoryRunArchive:
    _RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def save(self, run: VerifiedRun) -> ArchivedRun:
        self._validate_run_id(run.run_id)
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.root / run.run_id
        if destination.exists():
            raise RunArchiveError(f"Verified Run already exists: {run.run_id}")

        temporary = Path(tempfile.mkdtemp(prefix=f".{run.run_id}-", dir=self.root))
        try:
            predictions_path = temporary / "predictions.jsonl"
            payload = canonical_prediction_payload(run.predictions)
            if hashlib.sha256(payload).hexdigest() != run.predictions_sha256:
                raise RunArchiveError("Prediction evidence checksum changed before persistence.")
            predictions_path.write_bytes(payload)
            manifest_path = temporary / "manifest.json"
            manifest_path.write_text(
                json.dumps(self._manifest(run), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        return ArchivedRun(
            run_id=run.run_id,
            directory=destination,
            manifest_path=destination / "manifest.json",
            predictions_path=destination / "predictions.jsonl",
        )

    def source_status(self, run_id: str) -> SourceReferenceStatus:
        self._validate_run_id(run_id)
        manifest_path = self.root / run_id / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            source = manifest["source"]
            source_path = Path(source["path"])
            expected = str(source["sha256"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise RunArchiveError(f"Verified Run manifest is unavailable or invalid: {run_id}") from error
        if not source_path.is_file():
            return SourceReferenceStatus(SourceReferenceState.MISSING, expected)
        current = self._sha256(source_path)
        state = (
            SourceReferenceState.AVAILABLE
            if current == expected
            else SourceReferenceState.MODIFIED
        )
        return SourceReferenceStatus(state, expected, current)

    def list_entries(self) -> tuple[RunArchiveEntry, ...]:
        if not self.root.is_dir():
            return ()
        entries = []
        for directory in self.root.iterdir():
            if not directory.is_dir() or not self._RUN_ID.fullmatch(directory.name):
                continue
            manifest_path = directory / "manifest.json"
            try:
                manifest = self._read_manifest(manifest_path, directory.name)
                output = manifest["output"]
                entries.append(
                    RunArchiveEntry(
                        run_id=directory.name,
                        completed_at=str(manifest["completed_at"]),
                        source_file_name=str(manifest["source"]["file_name"]),
                        model_package_name=str(manifest["model_package"]["display_name"]),
                        model_package_version=str(manifest["model_package"]["version"]),
                        record_count=int(output["record_count"]),
                        pathogenic_count=int(output["pathogenic_count"]),
                        warning_count=len(manifest.get("warnings", ())),
                    )
                )
            except (RunArchiveError, KeyError, TypeError, ValueError):
                continue
        return tuple(sorted(entries, key=lambda item: item.completed_at, reverse=True))

    def load(self, run_id: str) -> LoadedVerifiedRun:
        self._validate_run_id(run_id)
        run_directory = (self.root / run_id).resolve()
        if run_directory.parent != self.root or not run_directory.is_dir():
            raise RunArchiveError(f"Verified Run not found: {run_id}")
        manifest = self._read_manifest(run_directory / "manifest.json", run_id)
        try:
            output = manifest["output"]
            if output["file"] != "predictions.jsonl":
                raise RunArchiveError("Verified Run declares an unsupported prediction file.")
            predictions_path = (run_directory / output["file"]).resolve()
            if predictions_path.parent != run_directory or not predictions_path.is_file():
                raise RunArchiveError("Verified Run prediction evidence is unavailable.")
            payload = predictions_path.read_bytes()
            expected_output_checksum = str(output["sha256"])
            if hashlib.sha256(payload).hexdigest() != expected_output_checksum:
                raise RunArchiveError("Verified Run prediction evidence checksum mismatch.")
            predictions = self._parse_predictions(payload)
            source = manifest["source"]
            package = manifest["model_package"]
            contract = manifest["inference_contract"]
            warnings = tuple(
                Finding(
                    code=str(value["code"]),
                    message=str(value["message"]),
                    columns=tuple(str(column) for column in value.get("columns", ())),
                )
                for value in manifest.get("warnings", ())
            )
            audit = TransformationAudit(
                tuple(
                    AuditEntry(
                        topic=str(value["topic"]),
                        summary=str(value["summary"]),
                        detail=str(value["detail"]),
                        severity=str(value.get("severity", "information")),
                    )
                    for value in manifest.get("transformation_audit", ())
                )
            )
            loaded = LoadedVerifiedRun(
                run_id=run_id,
                created_at=str(manifest["created_at"]),
                completed_at=str(manifest["completed_at"]),
                duration_ms=int(manifest["duration_ms"]),
                source_path=Path(source["path"]),
                source_file_name=str(source["file_name"]),
                source_sha256=str(source["sha256"]),
                source_row_count=int(source["row_count"]),
                source_column_count=int(source["column_count"]),
                model_package_name=str(package["display_name"]),
                model_package_version=str(package["version"]),
                model_package_manifest_checksum=str(package["manifest_sha256"]),
                inference_contract_id=str(contract["contract_id"]),
                inference_contract_version=str(contract["version"]),
                inference_contract_checksum=str(contract["checksum"]),
                release_threshold=float(contract["release_threshold"]),
                predictions_sha256=expected_output_checksum,
                predictions=predictions,
                warnings=warnings,
                transformation_audit=audit,
            )
            if len(predictions) != int(output["record_count"]):
                raise RunArchiveError("Verified Run prediction count does not match its manifest.")
            pathogenic_count = sum(
                record.prediction == "Pathogenic" for record in predictions
            )
            if pathogenic_count != int(output["pathogenic_count"]):
                raise RunArchiveError("Verified Run class counts do not match its manifest.")
            return loaded
        except RunArchiveError:
            raise
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as error:
            raise RunArchiveError(f"Verified Run is invalid: {run_id}") from error

    def _manifest(self, run: VerifiedRun) -> dict:
        pathogenic_count = sum(
            record.prediction == "Pathogenic" for record in run.predictions
        )
        return {
            "schema_version": 1,
            "run_id": run.run_id,
            "status": "verified",
            "created_at": run.created_at,
            "completed_at": run.completed_at,
            "duration_ms": run.duration_ms,
            "source": {
                "path": str(run.source.path),
                "file_name": run.source.file_name,
                "sha256": run.source.sha256,
                "row_count": run.source.row_count,
                "column_count": run.source.column_count,
                "delimiter": run.source.delimiter,
                "encoding": run.source.encoding,
                "last_modified": run.source.last_modified,
                "snapshot": {"included": run.source_snapshot_included},
            },
            "model_package": {
                "package_id": run.model_package_id,
                "display_name": run.model_package_name,
                "version": run.model_package_version,
                "manifest_sha256": run.model_package_manifest_checksum,
            },
            "inference_contract": {
                "contract_id": run.inference_contract_id,
                "version": run.inference_contract_version,
                "checksum": run.inference_contract_checksum,
                "release_threshold": run.release_threshold,
            },
            "output": {
                "file": "predictions.jsonl",
                "sha256": run.predictions_sha256,
                "record_count": len(run.predictions),
                "pathogenic_count": pathogenic_count,
                "benign_count": len(run.predictions) - pathogenic_count,
            },
            "warnings": [
                {
                    "code": warning.code,
                    "message": warning.message,
                    "columns": list(warning.columns),
                }
                for warning in run.warnings
            ],
            "transformation_audit": [
                {
                    "topic": entry.topic,
                    "summary": entry.summary,
                    "detail": entry.detail,
                    "severity": entry.severity,
                }
                for entry in run.transformation_audit.entries
            ],
        }

    def _read_manifest(self, manifest_path: Path, run_id: str) -> dict:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as error:
            raise RunArchiveError(
                f"Verified Run manifest is unavailable or invalid: {run_id}"
            ) from error
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema_version") != 1
            or manifest.get("status") != "verified"
            or manifest.get("run_id") != run_id
        ):
            raise RunArchiveError(f"Verified Run manifest identity is invalid: {run_id}")
        return manifest

    @staticmethod
    def _parse_predictions(payload: bytes) -> tuple[PredictionRecord, ...]:
        records = []
        for line_number, raw_line in enumerate(payload.decode("utf-8").splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                value = json.loads(raw_line)
                component_scores = {
                    str(name): float(score)
                    for name, score in value["component_scores"].items()
                }
                numeric_values = (
                    float(value["ensemble_score"]),
                    float(value["model_disagreement"]),
                    *component_scores.values(),
                )
                if not all(math.isfinite(number) for number in numeric_values):
                    raise ValueError("non-finite score")
                record = PredictionRecord(
                    source_row=int(value["source_row"]),
                    ensemble_score=numeric_values[0],
                    prediction=str(value["prediction"]),
                    component_scores=component_scores,
                    model_disagreement=numeric_values[1],
                )
                if record.prediction not in {"Pathogenic", "Benign"}:
                    raise ValueError("invalid prediction label")
                records.append(record)
            except (AttributeError, KeyError, TypeError, ValueError) as error:
                raise RunArchiveError(
                    f"Verified Run prediction line {line_number} is invalid."
                ) from error
        return tuple(records)

    @classmethod
    def _validate_run_id(cls, run_id: str) -> None:
        if not cls._RUN_ID.fullmatch(run_id):
            raise RunArchiveError("Verified Run identifier is invalid.")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
