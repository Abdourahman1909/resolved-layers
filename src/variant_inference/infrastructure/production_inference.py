from __future__ import annotations

import pickle
from typing import Any

from variant_inference.application.ports import SourceDataset
from variant_inference.domain.models import (
    FeatureKind,
    FeaturePresence,
    ModelPackageIdentity,
    PredictionRecord,
)


class ProductionInferenceError(RuntimeError):
    pass


class PickleEnsembleInference:
    """Run one integrity-validated CatBoost–LightGBM Model Package."""

    MODEL_ROLES = {
        "catboost": "catboost_model",
        "lightgbm": "lightgbm_model",
    }

    def __init__(self, trusted_manifest_checksums: set[str]) -> None:
        self._trusted_manifest_checksums = {
            value.strip().lower() for value in trusted_manifest_checksums if value.strip()
        }
        if not self._trusted_manifest_checksums:
            raise ValueError("At least one trusted Model Package manifest checksum is required.")

    def predict(
        self, source: SourceDataset, package: ModelPackageIdentity
    ) -> tuple[PredictionRecord, ...]:
        if package.manifest_checksum.lower() not in self._trusted_manifest_checksums:
            raise ProductionInferenceError(
                "Model Package manifest is not trusted for deterministic inference."
            )
        try:
            import numpy as np
            import pandas as pd
        except ImportError as error:  # pragma: no cover - packaging/runtime guard
            raise ProductionInferenceError(
                "Production inference requires the NumPy and pandas runtime."
            ) from error

        contract = package.contract
        source_columns = {name: index for index, name in enumerate(source.columns)}
        missing_required = tuple(
            feature.name
            for feature in contract.features
            if feature.presence is FeaturePresence.REQUIRED
            and feature.name not in source_columns
        )
        if missing_required:
            raise ProductionInferenceError(
                "Source Dataset is missing Required Model Features: "
                + ", ".join(missing_required)
            )

        # Read each source row once, not once per feature.
        #
        # The reader pages rows out of its store and caches only a few pages, so
        # walking every row for each of the 352 features in turn re-reads and
        # re-parses the whole dataset 352 times. On a 4,419-row file that was
        # 133 seconds of the run; done this way it is under a second, and the
        # values produced are identical.
        row_count = source.identity.row_count
        plan = tuple(
            (feature.name, source_columns.get(feature.name), feature.missing_representation)
            for feature in contract.features
        )
        values: dict[str, list[Any]] = {name: [] for name, _, _ in plan}
        for row_index in range(row_count):
            row = source.row_at(row_index)
            for name, column_index, missing in plan:
                values[name].append(row[column_index] if column_index is not None else missing)

        frame = pd.DataFrame(values, columns=[feature.name for feature in contract.features])
        categorical_features = []
        for feature in contract.features:
            if feature.kind is FeatureKind.NUMERIC:
                frame[feature.name] = pd.to_numeric(frame[feature.name], errors="coerce")
                continue
            categorical_features.append(feature)
            missing_value = feature.unknown_category or "Unknown"
            frame[feature.name] = frame[feature.name].map(
                lambda value: missing_value
                if value is None or not str(value).strip()
                else str(value)
            )

        models = self._load_models(package)
        component_scores: dict[str, Any] = {}
        for component, model in models.items():
            component_frame = frame.copy()
            for feature in categorical_features:
                if component == "catboost":
                    component_frame[feature.name] = component_frame[feature.name].astype(str)
                elif feature.allowed_categories:
                    component_frame[feature.name] = pd.Categorical(
                        component_frame[feature.name].astype(str),
                        categories=feature.allowed_categories,
                    )
                else:
                    component_frame[feature.name] = component_frame[feature.name].astype(
                        "category"
                    )
            probabilities = np.asarray(model.predict_proba(component_frame), dtype=float)
            if probabilities.shape != (source.identity.row_count, 2):
                raise ProductionInferenceError(
                    f"{component} returned probabilities with unexpected shape "
                    f"{probabilities.shape}."
                )
            component_scores[component] = probabilities[:, 1]

        ensemble_scores = np.zeros(source.identity.row_count, dtype=float)
        for component, scores in component_scores.items():
            ensemble_scores += contract.ensemble_weights[component] * scores
        disagreements = np.std(np.vstack(tuple(component_scores.values())), axis=0)

        records = []
        for index, ensemble_score in enumerate(ensemble_scores):
            score = round(float(ensemble_score), 12)
            records.append(
                PredictionRecord(
                    source_row=index + 1,
                    ensemble_score=score,
                    prediction=(
                        "Pathogenic"
                        if score >= contract.release_threshold
                        else "Benign"
                    ),
                    component_scores={
                        component: round(float(scores[index]), 12)
                        for component, scores in component_scores.items()
                    },
                    model_disagreement=round(float(disagreements[index]), 12),
                )
            )
        return tuple(records)

    def _load_models(self, package: ModelPackageIdentity) -> dict[str, Any]:
        artifacts_by_role = {artifact.role: artifact for artifact in package.artifacts}
        models = {}
        for component, role in self.MODEL_ROLES.items():
            artifact = artifacts_by_role.get(role)
            if artifact is None:
                raise ProductionInferenceError(
                    f"Model Package is missing the {role!r} artifact role."
                )
            artifact_path = package.root / artifact.path
            with artifact_path.open("rb") as handle:
                models[component] = pickle.load(handle)
        return models
