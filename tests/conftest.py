from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from variant_inference.domain.models import (
    FeatureKind,
    FeaturePresence,
    FeatureSpec,
    InferenceContract,
    ModelPackageIdentity,
    SourceIdentity,
)


class MemorySource:
    def __init__(self, columns: tuple[str, ...]) -> None:
        self.columns = columns
        self.column_types = tuple("text" for _ in columns)
        self.identity = SourceIdentity(
            path=Path("/tmp/synthetic.csv"),
            file_name="synthetic.csv",
            row_count=2,
            column_count=len(columns),
            sha256="0" * 64,
            delimiter="Comma (,)\n".strip(),
            encoding="UTF-8",
            last_modified="2026-08-28T12:00:00+03:00",
        )
        self.closed = False

    def row_at(self, source_row_index: int) -> tuple[str, ...]:
        return tuple(f"row-{source_row_index}-{name}" for name in self.columns)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def inference_contract() -> InferenceContract:
    return InferenceContract(
        contract_id="synthetic-contract",
        version="0.test",
        features=(
            FeatureSpec("required_numeric", FeaturePresence.REQUIRED, FeatureKind.NUMERIC),
            FeatureSpec(
                "required_category",
                FeaturePresence.REQUIRED,
                FeatureKind.CATEGORICAL,
                allowed_categories=("A", "B", "Unknown"),
                unknown_category="Unknown",
            ),
            FeatureSpec(
                "omissible_panel",
                FeaturePresence.OMISSIBLE,
                FeatureKind.CATEGORICAL,
                missing_representation="Unknown",
                allowed_categories=("Panel-A", "Unknown"),
                unknown_category="Unknown",
            ),
        ),
        ensemble_weights={"catboost": 0.5007, "lightgbm": 0.4993},
        release_threshold=0.61,
    )


@pytest.fixture
def model_package(inference_contract: InferenceContract) -> ModelPackageIdentity:
    return ModelPackageIdentity(
        package_id="synthetic-package",
        display_name="Synthetic development package",
        version="0.test",
        root=Path("/tmp/synthetic-package"),
        manifest_checksum=hashlib.sha256(b"synthetic").hexdigest(),
        contract=inference_contract,
    )
