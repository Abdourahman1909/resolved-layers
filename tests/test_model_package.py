from __future__ import annotations

import hashlib
import json

import pytest

from variant_inference.infrastructure.model_package import (
    JsonModelPackageRepository,
    ModelPackageValidationError,
)


def package_payload(artifact_hash: str) -> dict:
    return {
        "schema_version": 1,
        "package_id": "chl.synthetic",
        "display_name": "Synthetic package",
        "version": "0.test",
        "artifacts": [{"path": "synthetic-model.bin", "sha256": artifact_hash}],
        "inference_contract": {
            "contract_id": "chl.synthetic.contract",
            "version": "0.test",
            "features": [
                {"name": "feature_a", "presence": "required", "kind": "numeric"},
                {
                    "name": "panel",
                    "presence": "omissible",
                    "kind": "categorical",
                    "missing_representation": "Unknown",
                    "allowed_categories": ["A", "Unknown"],
                    "unknown_category": "Unknown",
                },
            ],
            "ensemble_weights": {"catboost": 0.5007, "lightgbm": 0.4993},
            "release_threshold": 0.61,
            "row_filtering": "none",
        },
    }


def test_manifest_and_artifact_integrity_are_validated(tmp_path):
    artifact = tmp_path / "synthetic-model.bin"
    artifact.write_bytes(b"not-a-real-model")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(package_payload(digest)), encoding="utf-8")

    package = JsonModelPackageRepository().load(manifest)

    assert package.display_name == "Synthetic package"
    assert package.contract.required_features[0].name == "feature_a"
    assert package.contract.release_threshold == 0.61


def test_tampered_artifact_is_rejected(tmp_path):
    artifact = tmp_path / "synthetic-model.bin"
    artifact.write_bytes(b"tampered")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(package_payload("0" * 64)), encoding="utf-8")

    with pytest.raises(ModelPackageValidationError, match="checksum mismatch"):
        JsonModelPackageRepository().load(manifest)


def test_artifact_symlink_cannot_escape_the_package(tmp_path):
    package_root = tmp_path / "package"
    package_root.mkdir()
    outside_artifact = tmp_path / "outside-model.bin"
    outside_artifact.write_bytes(b"outside the trusted package")
    (package_root / "synthetic-model.bin").symlink_to(outside_artifact)
    manifest = package_root / "manifest.json"
    manifest.write_text(
        json.dumps(package_payload(hashlib.sha256(outside_artifact.read_bytes()).hexdigest())),
        encoding="utf-8",
    )

    with pytest.raises(ModelPackageValidationError, match="remain inside the package"):
        JsonModelPackageRepository().load(manifest)
