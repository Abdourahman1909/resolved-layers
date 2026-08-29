from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


class FeaturePresence(str, Enum):
    REQUIRED = "required"
    OMISSIBLE = "omissible"


class FeatureKind(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"


class SourceValueFilterMode(str, Enum):
    EXACT = "exact"
    MISSING = "missing"
    UNRECOGNIZED = "unrecognized"


@dataclass(frozen=True)
class SourceIdentity:
    path: Path
    file_name: str
    row_count: int
    column_count: int
    sha256: str
    delimiter: str
    encoding: str
    last_modified: str


@dataclass(frozen=True)
class SourceValueFilter:
    column_index: int
    mode: SourceValueFilterMode
    value: str = ""
    recognized_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundTruthAuthorization:
    column_name: str
    pathogenic_value: str
    benign_value: str

    def __post_init__(self) -> None:
        if not self.column_name:
            raise ValueError("Ground-Truth Authorization requires a label column.")
        if not self.pathogenic_value or not self.benign_value:
            raise ValueError("Pathogenic and Benign mappings must both be explicit.")
        if self.pathogenic_value == self.benign_value:
            raise ValueError("Pathogenic and Benign must map to different source values.")


@dataclass(frozen=True)
class LabelCoverage:
    total: int
    pathogenic: int
    benign: int
    missing: int
    unrecognized: int

    @property
    def recognized(self) -> int:
        return self.pathogenic + self.benign


@dataclass(frozen=True)
class GroupBreakdown:
    value: str
    total: int
    share: float
    pathogenic: int = 0
    benign: int = 0
    missing_or_unrecognized: int = 0


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    presence: FeaturePresence
    kind: FeatureKind
    missing_representation: str | None = None
    allowed_categories: tuple[str, ...] = ()
    unknown_category: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FeatureSpec":
        return cls(
            name=str(value["name"]),
            presence=FeaturePresence(value["presence"]),
            kind=FeatureKind(value["kind"]),
            missing_representation=(
                None
                if value.get("missing_representation") is None
                else str(value["missing_representation"])
            ),
            allowed_categories=tuple(str(item) for item in value.get("allowed_categories", ())),
            unknown_category=(
                None if value.get("unknown_category") is None else str(value["unknown_category"])
            ),
        )


@dataclass(frozen=True)
class InferenceContract:
    contract_id: str
    version: str
    features: tuple[FeatureSpec, ...]
    ensemble_weights: Mapping[str, float]
    release_threshold: float
    row_filtering: str = "none"
    checksum: str = ""
    component_input_policy: Mapping[str, Mapping[str, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        names = [feature.name for feature in self.features]
        if not names:
            raise ValueError("An Inference Contract must declare at least one Model Feature.")
        if len(names) != len(set(names)):
            raise ValueError("Inference Contract feature names must be unique.")
        if not 0.0 <= self.release_threshold <= 1.0:
            raise ValueError("Release Threshold must be between zero and one.")
        if self.row_filtering != "none":
            raise ValueError("This release only accepts contracts that preserve every Source Row.")
        if not self.ensemble_weights or any(weight < 0 for weight in self.ensemble_weights.values()):
            raise ValueError("Ensemble weights must be present and non-negative.")
        if abs(sum(self.ensemble_weights.values()) - 1.0) > 1e-6:
            raise ValueError("Ensemble weights must sum to one.")
        for feature in self.features:
            if feature.presence is FeaturePresence.OMISSIBLE and feature.missing_representation is None:
                raise ValueError(
                    f"Omissible feature {feature.name!r} must declare its missing representation."
                )
            if feature.allowed_categories and feature.kind is not FeatureKind.CATEGORICAL:
                raise ValueError(f"Only categorical features may declare category mappings: {feature.name}")

    @property
    def required_features(self) -> tuple[FeatureSpec, ...]:
        return tuple(item for item in self.features if item.presence is FeaturePresence.REQUIRED)

    @property
    def omissible_features(self) -> tuple[FeatureSpec, ...]:
        return tuple(item for item in self.features if item.presence is FeaturePresence.OMISSIBLE)


@dataclass(frozen=True)
class ModelPackageIdentity:
    package_id: str
    display_name: str
    version: str
    root: Path
    manifest_checksum: str
    contract: InferenceContract
    artifacts: tuple["ModelArtifact", ...] = ()


@dataclass(frozen=True)
class ModelArtifact:
    role: str
    path: Path
    sha256: str


@dataclass(frozen=True)
class PredictionRecord:
    source_row: int
    ensemble_score: float
    prediction: str
    component_scores: Mapping[str, float]
    model_disagreement: float


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContractFit:
    required_count: int
    available_required_count: int
    missing_required: tuple[str, ...]
    missing_omissible: tuple[str, ...]
    surplus_columns: tuple[str, ...]
    blocking_issues: tuple[Finding, ...] = ()
    warnings: tuple[Finding, ...] = ()

    @property
    def is_compatible(self) -> bool:
        return not self.blocking_issues


@dataclass(frozen=True)
class AuditEntry:
    topic: str
    summary: str
    detail: str
    severity: str = "information"


@dataclass(frozen=True)
class TransformationAudit:
    entries: tuple[AuditEntry, ...] = field(default_factory=tuple)

    def summary_for(self, topic: str, default: str = "—") -> str:
        return next((entry.summary for entry in self.entries if entry.topic == topic), default)
