from __future__ import annotations

from dataclasses import dataclass

from variant_inference.application.ports import SourceDataset
from variant_inference.domain.models import (
    ContractFit,
    InferenceContract,
    ModelPackageIdentity,
    TransformationAudit,
)
from variant_inference.domain.services import SchemaCompatibilityService, TransformationAuditService


@dataclass
class SourceReviewSession:
    source: SourceDataset | None = None
    package: ModelPackageIdentity | None = None
    fit: ContractFit | None = None
    audit: TransformationAudit | None = None
    operator_confirmed: bool = False

    def load_source(
        self,
        source: SourceDataset,
        package: ModelPackageIdentity | None,
        compatibility: SchemaCompatibilityService | None = None,
        audits: TransformationAuditService | None = None,
    ) -> None:
        if self.source is not None and self.source is not source:
            self.source.close()
        self.source = source
        self.package = package
        self.operator_confirmed = False
        if package is None:
            self.fit = None
            self.audit = None
            return
        compatibility = compatibility or SchemaCompatibilityService()
        audits = audits or TransformationAuditService()
        self.fit = compatibility.evaluate(source.columns, package.contract)
        self.audit = audits.build(package.contract, self.fit)

    def set_operator_confirmation(self, confirmed: bool) -> None:
        self.operator_confirmed = bool(confirmed)

    @property
    def can_confirm(self) -> bool:
        return bool(self.source and self.package and self.fit and self.fit.is_compatible)

    @property
    def run_enabled(self) -> bool:
        return self.can_confirm and self.operator_confirmed

    def close(self) -> None:
        if self.source is not None:
            self.source.close()
        self.source = None
        self.fit = None
        self.audit = None
        self.operator_confirmed = False

