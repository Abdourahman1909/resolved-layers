from __future__ import annotations

from collections import Counter
from typing import Sequence

from variant_inference.domain.models import (
    AuditEntry,
    ContractFit,
    FeatureKind,
    Finding,
    InferenceContract,
    TransformationAudit,
)


class SchemaCompatibilityService:
    """Compare Source Dataset columns with policy frozen in an Inference Contract."""

    def evaluate(self, source_columns: Sequence[str], contract: InferenceContract) -> ContractFit:
        counts = Counter(source_columns)
        source_names = set(source_columns)
        contract_names = {item.name for item in contract.features}

        missing_required = tuple(
            item.name for item in contract.required_features if item.name not in source_names
        )
        missing_omissible = tuple(
            item.name for item in contract.omissible_features if item.name not in source_names
        )
        surplus = tuple(dict.fromkeys(name for name in source_columns if name not in contract_names))
        duplicates = tuple(name for name, count in counts.items() if count > 1)

        blockers: list[Finding] = []
        warnings: list[Finding] = []
        if missing_required:
            blockers.append(
                Finding(
                    code="missing_required_features",
                    message=f"{len(missing_required)} Required Model Feature(s) are absent.",
                    columns=missing_required,
                )
            )
        if duplicates:
            blockers.append(
                Finding(
                    code="duplicate_source_columns",
                    message="Duplicate column names make feature alignment ambiguous.",
                    columns=duplicates,
                )
            )
        if missing_omissible:
            warnings.append(
                Finding(
                    code="missing_omissible_features",
                    message=(
                        f"{len(missing_omissible)} Omissible Model Feature(s) will use only "
                        "their contract-declared missing representation."
                    ),
                    columns=missing_omissible,
                )
            )
        if surplus:
            warnings.append(
                Finding(
                    code="surplus_context_columns",
                    message=f"{len(surplus)} surplus column(s) remain inspectable and excluded from inference.",
                    columns=surplus,
                )
            )

        return ContractFit(
            required_count=len(contract.required_features),
            available_required_count=len(contract.required_features) - len(missing_required),
            missing_required=missing_required,
            missing_omissible=missing_omissible,
            surplus_columns=surplus,
            blocking_issues=tuple(blockers),
            warnings=tuple(warnings),
        )


class TransformationAuditService:
    """Describe normalization without changing or duplicating the raw Source Dataset."""

    def build(self, contract: InferenceContract, fit: ContractFit) -> TransformationAudit:
        categorical_count = sum(
            1 for feature in contract.features if feature.kind is FeatureKind.CATEGORICAL
        )
        mapped_count = sum(1 for feature in contract.features if feature.allowed_categories)
        missing_summary = (
            "Contract defaults pending confirmation"
            if fit.missing_omissible
            else "Native missing values preserved"
        )
        missing_detail = (
            ", ".join(fit.missing_omissible)
            if fit.missing_omissible
            else "No absent Omissible Model Features require a supplied representation."
        )
        alignment_count = len(contract.features) - len(fit.missing_required) - len(fit.missing_omissible)

        return TransformationAudit(
            entries=(
                AuditEntry(
                    topic="type_handling",
                    summary="Normalized copy only",
                    detail="Raw values remain unchanged; numeric and categorical handling is model-specific.",
                ),
                AuditEntry(
                    topic="missing_values",
                    summary=missing_summary,
                    detail=missing_detail,
                    severity="warning" if fit.missing_omissible else "information",
                ),
                AuditEntry(
                    topic="category_mapping",
                    summary=f"{mapped_count} fixed · {categorical_count} categorical",
                    detail="Category mappings are read only from the validated Inference Contract.",
                ),
                AuditEntry(
                    topic="column_mapping",
                    summary=f"Contract alignment ({alignment_count}/{len(contract.features)})",
                    detail="Model Features are aligned by declared name and reordered to contract order.",
                ),
                AuditEntry(
                    topic="row_filtering",
                    summary="None",
                    detail="Every Source Row remains present and in its original official export order.",
                ),
            )
        )
