from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from variant_inference.application.verified_run import canonical_prediction_payload
from variant_inference.domain.models import (
    ArchivedRun,
    SourceReferenceState,
    SourceReferenceStatus,
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
