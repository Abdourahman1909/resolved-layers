from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from variant_inference.domain.models import (
    ArchivedRun,
    EvaluationReport,
    EvaluationSourceEvidence,
    GroundTruthAuthorization,
    LabelCoverage,
    LoadedVerifiedRun,
    ModelPackageIdentity,
    PredictionRecord,
    RunArchiveEntry,
    SourceIdentity,
    SourceReferenceStatus,
    SourceValueFilter,
    VerifiedRun,
)


class SourceDataset(Protocol):
    identity: SourceIdentity
    columns: tuple[str, ...]
    column_types: tuple[str, ...]
    missing_cell_count: int
    rows_with_missing: int

    def row_at(self, source_row_index: int) -> tuple[str, ...]: ...
    def value_counts(self, column_index: int) -> tuple[tuple[str, int], ...]: ...
    def paired_value_counts(
        self, first_column_index: int, second_column_index: int
    ) -> tuple[tuple[str, str, int], ...]: ...
    def matching_source_rows(self, filters: Sequence[SourceValueFilter]) -> tuple[int, ...]: ...
    def close(self) -> None: ...


class SourceDatasetReader(Protocol):
    def open(self, path: Path) -> SourceDataset: ...


class ModelPackageRepository(Protocol):
    def load(self, manifest_path: Path) -> ModelPackageIdentity: ...


class DeterministicInference(Protocol):
    def predict(
        self, source: SourceDataset, package: ModelPackageIdentity
    ) -> Sequence[PredictionRecord]: ...


class RunArchive(Protocol):
    def save(self, run: VerifiedRun) -> ArchivedRun: ...
    def load(self, run_id: str) -> LoadedVerifiedRun: ...
    def list_entries(self) -> Sequence[RunArchiveEntry]: ...
    def source_status(self, run_id: str) -> SourceReferenceStatus: ...


class EvaluationService(Protocol):
    def prepare(self, run: LoadedVerifiedRun) -> EvaluationSourceEvidence: ...
    def label_values(self, run: LoadedVerifiedRun, column_name: str) -> tuple[str, ...]: ...
    def preview(
        self,
        run: LoadedVerifiedRun,
        proposed_mapping: GroundTruthAuthorization,
    ) -> LabelCoverage: ...
    def evaluate(
        self,
        run: LoadedVerifiedRun,
        authorization: GroundTruthAuthorization,
    ) -> EvaluationReport: ...


class CompetitionExportProfileRepository(Protocol):
    def active_profile(self) -> Mapping[str, Any] | None: ...


class ReadOnlyInvestigationEvidence(Protocol):
    def query(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...
