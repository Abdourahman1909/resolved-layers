from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from variant_inference.domain.models import ModelPackageIdentity, SourceIdentity


class SourceDataset(Protocol):
    identity: SourceIdentity
    columns: tuple[str, ...]
    column_types: tuple[str, ...]

    def row_at(self, source_row_index: int) -> tuple[str, ...]: ...
    def close(self) -> None: ...


class SourceDatasetReader(Protocol):
    def open(self, path: Path) -> SourceDataset: ...


class ModelPackageRepository(Protocol):
    def load(self, manifest_path: Path) -> ModelPackageIdentity: ...


class DeterministicInference(Protocol):
    def predict(self, source: SourceDataset, package: ModelPackageIdentity) -> Sequence[Mapping[str, Any]]: ...


class RunArchive(Protocol):
    def save_manifest(self, run_manifest: Mapping[str, Any]) -> str: ...


class EvaluationService(Protocol):
    def evaluate(self, predictions: Sequence[int], ground_truth: Sequence[int]) -> Mapping[str, float]: ...


class CompetitionExportProfileRepository(Protocol):
    def active_profile(self) -> Mapping[str, Any] | None: ...


class ReadOnlyInvestigationEvidence(Protocol):
    def query(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...

