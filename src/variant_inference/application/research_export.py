"""Write a Verified Run out as a file someone else can open.

Research Export preserves every original Source Dataset column beside the
immutable predictions, so a result can be read in a spreadsheet, analysed
elsewhere, or attached to a report. It needs no organizer format and guesses
none: Competition Export remains a separate, deliberately unimplemented
surface awaiting the official instructions.

Two boundaries matter here.

Source values are read only while the archived SHA-256 still matches the file
on disk, the same rule the Variant Inspector and Evaluation follow. An export
built from a modified source would silently misattribute values to rows.

Row order is Source Row order, always. Table sorting, grouping, and cohort
filters are investigation tools; they never reach an exported file.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from variant_inference.application.ports import SourceDatasetReader
from variant_inference.domain.models import LoadedVerifiedRun

SOURCE_ROW_COLUMN = "source_row"
PREDICTION_COLUMNS = (
    "prediction",
    "ensemble_score",
    "model_disagreement",
)
COMPONENT_COLUMN_TEMPLATE = "{component}_score"
DISAMBIGUATION_SUFFIX = "__resolved_layers"

SCORE_PRECISION = 12


class ResearchExportError(RuntimeError):
    """The export could not be produced from trustworthy evidence."""


@dataclass(frozen=True)
class ResearchExportReport:
    csv_path: Path
    evidence_path: Path
    row_count: int
    source_column_count: int
    added_columns: tuple[str, ...]


class ResearchExportService:
    """Join immutable predictions to their exact original Source Rows."""

    def __init__(self, reader: SourceDatasetReader) -> None:
        self._reader = reader

    def export(self, run: LoadedVerifiedRun, destination: Path) -> ResearchExportReport:
        destination = Path(destination)
        if destination.suffix.lower() != ".csv":
            destination = destination.with_suffix(".csv")

        source = self._open_verified_source(run)
        try:
            report = self._write(run, source, destination)
        finally:
            source.close()
        return report

    # Source access --------------------------------------------------------

    def _open_verified_source(self, run: LoadedVerifiedRun):
        if not run.source_path.is_file():
            raise ResearchExportError(
                "The original Source Dataset is missing, so its columns cannot be exported."
            )
        if self._checksum(run.source_path) != run.source_sha256:
            raise ResearchExportError(
                "The original Source Dataset has changed since this run, so its columns "
                "can no longer be attributed to these predictions."
            )
        try:
            source = self._reader.open(run.source_path)
        except (OSError, ValueError) as error:
            raise ResearchExportError(
                "The original Source Dataset could not be opened for export."
            ) from error

        if len(source.columns) != run.source_column_count:
            source.close()
            raise ResearchExportError(
                "The original Source Dataset no longer has the dimensions recorded for this run."
            )
        return source

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    # Writing --------------------------------------------------------------

    def _write(self, run: LoadedVerifiedRun, source, destination: Path) -> ResearchExportReport:
        components = self._component_names(run)
        added = self._added_columns(source.columns, components)
        header = [*source.columns, *added]

        destination.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(
            dir=str(destination.parent), prefix=destination.name, suffix=".tmp"
        )
        written = 0
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                # Predictions are already stored in Source Row order, and the
                # archive rejects a run with missing or reordered rows, so
                # iterating them preserves official order without re-sorting.
                for record in run.predictions:
                    row = source.row_at(record.source_row - 1)
                    writer.writerow([*row, *self._prediction_values(record, components)])
                    written += 1
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

        evidence_path = self._write_evidence(run, destination, header, written)
        return ResearchExportReport(
            csv_path=destination,
            evidence_path=evidence_path,
            row_count=written,
            source_column_count=len(source.columns),
            added_columns=tuple(added),
        )

    @staticmethod
    def _component_names(run: LoadedVerifiedRun) -> tuple[str, ...]:
        if not run.predictions:
            return ()
        return tuple(sorted(run.predictions[0].component_scores))

    def _added_columns(self, source_columns, components: tuple[str, ...]) -> list[str]:
        """Name the appended columns without ever colliding with a source column.

        A Source Dataset may legitimately contain a column called `prediction`.
        Renaming ours keeps every original column intact and unshadowed.
        """
        taken = set(source_columns)
        names: list[str] = []
        preferred = [
            SOURCE_ROW_COLUMN,
            *PREDICTION_COLUMNS,
            *(COMPONENT_COLUMN_TEMPLATE.format(component=name) for name in components),
        ]
        for candidate in preferred:
            name = candidate
            while name in taken:
                name = f"{name}{DISAMBIGUATION_SUFFIX}"
            taken.add(name)
            names.append(name)
        return names

    @staticmethod
    def _prediction_values(record, components: tuple[str, ...]) -> list[str]:
        def number(value: float) -> str:
            return f"{value:.{SCORE_PRECISION}f}".rstrip("0").rstrip(".")

        return [
            str(record.source_row),
            record.prediction,
            number(record.ensemble_score),
            number(record.model_disagreement),
            *(number(record.component_scores[name]) for name in components),
        ]

    def _write_evidence(
        self,
        run: LoadedVerifiedRun,
        destination: Path,
        header: list[str],
        row_count: int,
    ) -> Path:
        """Record what produced this file, beside it.

        Traceability lives in a sidecar rather than repeated on every row, so
        the CSV stays directly readable by ordinary analysis tools.
        """
        evidence_path = destination.with_suffix(".evidence.json")
        payload = {
            "export_kind": "research",
            "note": (
                "Research Export. Not a Competition Export and not an official "
                "submission format."
            ),
            "run_id": run.run_id,
            "completed_at": run.completed_at,
            "row_count": row_count,
            "row_order": "source_row",
            "columns": header,
            "source": {
                "file_name": run.source_file_name,
                "path": str(run.source_path),
                "sha256": run.source_sha256,
                "row_count": run.source_row_count,
                "column_count": run.source_column_count,
            },
            "model_package": {
                "name": run.model_package_name,
                "version": run.model_package_version,
                "manifest_sha256": run.model_package_manifest_checksum,
            },
            "inference_contract": {
                "id": run.inference_contract_id,
                "version": run.inference_contract_version,
                "checksum": run.inference_contract_checksum,
            },
            "release_threshold": run.release_threshold,
            "predictions_sha256": run.predictions_sha256,
        }
        evidence_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return evidence_path
