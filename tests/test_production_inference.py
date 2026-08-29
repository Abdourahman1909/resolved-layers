from __future__ import annotations

import hashlib
import json
import pickle

import numpy as np
import pytest

from variant_inference.infrastructure.csv_source import CsvSourceReader
from variant_inference.infrastructure.model_package import JsonModelPackageRepository
from variant_inference.infrastructure.production_inference import (
    PickleEnsembleInference,
    ProductionInferenceError,
)


class SyntheticCatBoostModel:
    def predict_proba(self, frame):
        assert list(frame.columns) == ["Feature_A", "Category"]
        assert "label" not in frame.columns
        scores = frame["Feature_A"].astype(float).to_numpy()
        return np.column_stack((1.0 - scores, scores))


class SyntheticLightGbmModel:
    def predict_proba(self, frame):
        assert list(frame.columns) == ["Feature_A", "Category"]
        assert "label" not in frame.columns
        scores = 0.5 * frame["Feature_A"].astype(float).to_numpy() + 0.25
        return np.column_stack((1.0 - scores, scores))


def test_inference_preserves_source_rows_and_excludes_context_columns(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text(
        "label,Feature_A,Category,Research_Note\n"
        "1,0.20,A,first source row\n"
        "0,0.80,B,second source row\n",
        encoding="utf-8",
    )

    artifacts = {
        "catboost_model": ("catboost_final.pkl", SyntheticCatBoostModel()),
        "lightgbm_model": ("lightgbm_final.pkl", SyntheticLightGbmModel()),
    }
    artifact_entries = []
    for role, (file_name, model) in artifacts.items():
        artifact_path = tmp_path / file_name
        artifact_path.write_bytes(pickle.dumps(model))
        artifact_entries.append(
            {
                "role": role,
                "path": file_name,
                "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            }
        )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_id": "chl.synthetic.inference",
                "display_name": "Synthetic inference package",
                "version": "0.test",
                "artifacts": artifact_entries,
                "inference_contract": {
                    "contract_id": "chl.synthetic.inference.contract",
                    "version": "0.test",
                    "features": [
                        {
                            "name": "Feature_A",
                            "presence": "required",
                            "kind": "numeric",
                        },
                        {
                            "name": "Category",
                            "presence": "required",
                            "kind": "categorical",
                            "allowed_categories": ["A", "B"],
                            "unknown_category": "Unknown",
                        },
                    ],
                    "ensemble_weights": {"catboost": 0.5, "lightgbm": 0.5},
                    "release_threshold": 0.6,
                    "row_filtering": "none",
                    "component_input_policy": {
                        "catboost": {"categorical_missing": "Unknown"},
                        "lightgbm": {"categorical_unseen": "missing"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    package = JsonModelPackageRepository().load(manifest_path)
    assert package.contract.component_input_policy["lightgbm"]["categorical_unseen"] == "missing"
    source = CsvSourceReader().open(source_path)
    try:
        predictions = PickleEnsembleInference(
            trusted_manifest_checksums={package.manifest_checksum}
        ).predict(source, package)
    finally:
        source.close()

    assert [record.source_row for record in predictions] == [1, 2]
    assert [record.prediction for record in predictions] == ["Benign", "Pathogenic"]
    assert [record.ensemble_score for record in predictions] == [0.275, 0.725]
    assert predictions[0].component_scores == {
        "catboost": 0.2,
        "lightgbm": 0.35,
    }


def test_untrusted_manifest_is_rejected_before_model_deserialization(tmp_path):
    artifact = tmp_path / "synthetic-model.bin"
    artifact.write_bytes(b"not a pickle")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(package_payload(hashlib.sha256(artifact.read_bytes()).hexdigest())),
        encoding="utf-8",
    )
    package = JsonModelPackageRepository().load(manifest)

    with pytest.raises(ProductionInferenceError, match="not trusted"):
        PickleEnsembleInference(
            trusted_manifest_checksums={"0" * 64}
        ).predict(None, package)


def package_payload(artifact_hash: str) -> dict:
    return {
        "schema_version": 1,
        "package_id": "chl.synthetic.untrusted",
        "display_name": "Synthetic untrusted package",
        "version": "0.test",
        "artifacts": [
            {
                "role": "catboost_model",
                "path": "synthetic-model.bin",
                "sha256": artifact_hash,
            }
        ],
        "inference_contract": {
            "contract_id": "chl.synthetic.untrusted.contract",
            "version": "0.test",
            "features": [
                {"name": "Feature_A", "presence": "required", "kind": "numeric"}
            ],
            "ensemble_weights": {"catboost": 0.5, "lightgbm": 0.5},
            "release_threshold": 0.6,
            "row_filtering": "none",
        },
    }
