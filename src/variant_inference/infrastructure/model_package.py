from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from variant_inference.domain.models import (
    FeatureSpec,
    InferenceContract,
    ModelArtifact,
    ModelPackageIdentity,
)


class ModelPackageValidationError(ValueError):
    pass


class JsonModelPackageRepository:
    """Validate a declarative package manifest before any model runtime is loaded."""

    SUPPORTED_SCHEMA_VERSION = 1

    def load(self, manifest_path: Path) -> ModelPackageIdentity:
        manifest_path = Path(manifest_path).expanduser().resolve()
        if not manifest_path.is_file():
            raise ModelPackageValidationError(f"Model Package manifest not found: {manifest_path}")
        raw = manifest_path.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ModelPackageValidationError("Model Package manifest must be valid UTF-8 JSON.") from error
        if payload.get("schema_version") != self.SUPPORTED_SCHEMA_VERSION:
            raise ModelPackageValidationError("Unsupported Model Package manifest schema version.")

        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ModelPackageValidationError("A Model Package must declare integrity-checked artifacts.")
        validated_artifacts = tuple(
            self._validate_artifact(manifest_path.parent, artifact) for artifact in artifacts
        )

        contract_payload = payload.get("inference_contract")
        if not isinstance(contract_payload, dict):
            raise ModelPackageValidationError("Model Package is missing its Inference Contract.")
        contract_checksum = self._canonical_checksum(contract_payload)
        declared_checksum = contract_payload.get("checksum", "")
        checksum_payload = dict(contract_payload)
        checksum_payload.pop("checksum", None)
        calculated_contract_checksum = self._canonical_checksum(checksum_payload)
        if declared_checksum and declared_checksum != calculated_contract_checksum:
            raise ModelPackageValidationError("Inference Contract checksum does not match its content.")

        try:
            contract = InferenceContract(
                contract_id=str(contract_payload["contract_id"]),
                version=str(contract_payload["version"]),
                features=tuple(
                    FeatureSpec.from_mapping(item) for item in contract_payload["features"]
                ),
                ensemble_weights={
                    str(name): float(weight)
                    for name, weight in contract_payload["ensemble_weights"].items()
                },
                release_threshold=float(contract_payload["release_threshold"]),
                row_filtering=str(contract_payload.get("row_filtering", "none")),
                checksum=declared_checksum or contract_checksum,
                component_input_policy={
                    str(component): {
                        str(key): str(value) for key, value in policy.items()
                    }
                    for component, policy in contract_payload.get(
                        "component_input_policy", {}
                    ).items()
                },
            )
            return ModelPackageIdentity(
                package_id=str(payload["package_id"]),
                display_name=str(payload["display_name"]),
                version=str(payload["version"]),
                root=manifest_path.parent,
                manifest_checksum=hashlib.sha256(raw).hexdigest(),
                contract=contract,
                artifacts=validated_artifacts,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ModelPackageValidationError(f"Invalid Model Package contract: {error}") from error

    def _validate_artifact(self, root: Path, artifact: Mapping[str, Any]) -> ModelArtifact:
        try:
            relative_path = Path(str(artifact["path"]))
            expected = str(artifact["sha256"]).lower()
        except (KeyError, TypeError) as error:
            raise ModelPackageValidationError("Every artifact needs a relative path and SHA-256.") from error
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ModelPackageValidationError("Model Package artifact paths must remain inside the package.")
        resolved_root = root.resolve()
        artifact_path = (resolved_root / relative_path).resolve()
        if not artifact_path.is_relative_to(resolved_root):
            raise ModelPackageValidationError(
                "Model Package artifact paths must remain inside the package."
            )
        if not artifact_path.is_file():
            raise ModelPackageValidationError(f"Model Package artifact missing: {relative_path}")
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if digest != expected:
            raise ModelPackageValidationError(f"Model Package artifact checksum mismatch: {relative_path}")
        return ModelArtifact(
            role=str(artifact.get("role", "")),
            path=relative_path,
            sha256=expected,
        )

    def _canonical_checksum(self, payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
