from __future__ import annotations

from variant_inference.application.ports import RunArchive, SourceDataset, SourceDatasetReader
from variant_inference.domain.models import (
    LoadedVerifiedRun,
    SourceFieldEvidence,
    SourceReferenceState,
    SourceReferenceStatus,
    SourceRowEvidence,
)


class SourceRowEvidenceError(RuntimeError):
    pass


class SourceRowEvidenceService:
    """Read one archived Source Row without changing the source or Verified Run."""

    def __init__(self, archive: RunArchive, reader: SourceDatasetReader) -> None:
        self._archive = archive
        self._reader = reader
        self._source: SourceDataset | None = None
        self._run_id = ""
        self._source_signature: tuple[int, int, int, int, int] | None = None

    def read(self, run: LoadedVerifiedRun, source_row: int) -> SourceRowEvidence:
        if not 1 <= source_row <= run.source_row_count:
            raise SourceRowEvidenceError(
                f"Source Row {source_row} is outside Verified Run {run.run_id}."
            )

        if self._source is not None and self._run_id == run.run_id:
            current_signature = self._file_signature(run.source_path)
            if current_signature == self._source_signature:
                return self._available(run, source_row, self._source, run.source_sha256)
            status = self._archive.source_status(run.run_id)
            if status.state is not SourceReferenceState.AVAILABLE:
                self._clear_source()
                return self._unavailable(source_row, status)
            # Metadata changed, but the checksum proves the bytes are still exact.
            self._source_signature = current_signature
            return self._available(run, source_row, self._source, status.current_sha256)

        status = self._archive.source_status(run.run_id)
        if status.state is not SourceReferenceState.AVAILABLE:
            self._clear_source()
            return self._unavailable(source_row, status)
        signature_before = self._file_signature(run.source_path)
        source = self._source_for(run)
        signature_after = self._file_signature(run.source_path)
        if signature_before != signature_after:
            self._clear_source()
            raise SourceRowEvidenceError(
                "Original Source Dataset changed while it was being opened. "
                "Select the record again to re-verify it."
            )
        if (
            source.identity.sha256 != run.source_sha256
            or source.identity.row_count != run.source_row_count
            or source.identity.column_count != run.source_column_count
        ):
            current = source.identity.sha256
            self._clear_source()
            return SourceRowEvidence(
                source_row=source_row,
                state=SourceReferenceState.MODIFIED,
                expected_sha256=run.source_sha256,
                current_sha256=current,
                detail=(
                    "Original Source Dataset identity or dimensions no longer match "
                    "the immutable Verified Run. Row values were not read."
                ),
            )

        self._source_signature = signature_after
        return self._available(run, source_row, source, source.identity.sha256)

    @staticmethod
    def _available(
        run: LoadedVerifiedRun,
        source_row: int,
        source: SourceDataset,
        current_sha256: str,
    ) -> SourceRowEvidence:
        row = source.row_at(source_row - 1)
        fields = tuple(
            SourceFieldEvidence(name, value, value_type)
            for name, value, value_type in zip(
                source.columns, row, source.column_types, strict=True
            )
        )
        return SourceRowEvidence(
            source_row=source_row,
            state=SourceReferenceState.AVAILABLE,
            expected_sha256=run.source_sha256,
            current_sha256=current_sha256,
            detail=(
                "Checksum-valid original Source Row recovered through read-only source access."
            ),
            fields=fields,
        )

    def close(self) -> None:
        self._clear_source()

    def _source_for(self, run: LoadedVerifiedRun) -> SourceDataset:
        if self._source is not None and self._run_id == run.run_id:
            return self._source
        self._clear_source()
        try:
            source = self._reader.open(run.source_path)
        except (OSError, ValueError) as error:
            raise SourceRowEvidenceError(
                "Original Source Dataset could not be opened safely for inspection."
            ) from error
        self._source = source
        self._run_id = run.run_id
        return source

    def _clear_source(self) -> None:
        if self._source is not None:
            self._source.close()
        self._source = None
        self._run_id = ""
        self._source_signature = None

    @staticmethod
    def _file_signature(path) -> tuple[int, int, int, int, int] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return (
            int(stat.st_dev),
            int(stat.st_ino),
            int(stat.st_size),
            int(stat.st_mtime_ns),
            int(stat.st_ctime_ns),
        )

    @staticmethod
    def _unavailable(
        source_row: int, status: SourceReferenceStatus
    ) -> SourceRowEvidence:
        if status.state is SourceReferenceState.MISSING:
            detail = (
                "Original Source Dataset is missing at its archived path. "
                "No source values were read."
            )
        else:
            detail = (
                "Original Source Dataset checksum differs from the immutable Verified Run. "
                "No source values were read."
            )
        return SourceRowEvidence(
            source_row=source_row,
            state=status.state,
            expected_sha256=status.expected_sha256,
            current_sha256=status.current_sha256,
            detail=detail,
        )
