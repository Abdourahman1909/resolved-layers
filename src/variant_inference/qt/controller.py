from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from variant_inference.application.source_review import SourceReviewSession
from variant_inference.domain.models import ModelPackageIdentity
from variant_inference.infrastructure.csv_source import CsvSourceError, CsvSourceReader
from variant_inference.qt.table_model import CsvTableModel


class SourceReviewController(QObject):
    stateChanged = Signal()

    def __init__(
        self,
        table_model: CsvTableModel,
        package: ModelPackageIdentity | None,
        package_error: str = "",
        identity_reference: Path | None = None,
    ) -> None:
        super().__init__()
        self._table_model = table_model
        self._reader = CsvSourceReader()
        self._session = SourceReviewSession(package=package)
        self._package = package
        self._package_error = package_error
        self._status_message = "Open a Source Dataset to begin review."
        self._status_kind = "neutral"
        self._identity_reference = identity_reference

    def _emit(self) -> None:
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def hasSource(self) -> bool:  # noqa: N802
        return self._session.source is not None

    @Property(str, notify=stateChanged)
    def fileName(self) -> str:  # noqa: N802
        return self._identity("file_name")

    @Property(str, notify=stateChanged)
    def sourcePath(self) -> str:  # noqa: N802
        source = self._session.source
        return str(source.identity.path) if source else ""

    @Property(int, notify=stateChanged)
    def rowCount(self) -> int:  # noqa: N802
        source = self._session.source
        return source.identity.row_count if source else 0

    @Property(int, notify=stateChanged)
    def columnCount(self) -> int:  # noqa: N802
        source = self._session.source
        return source.identity.column_count if source else 0

    @Property(str, notify=stateChanged)
    def checksum(self) -> str:
        return self._identity("sha256")

    @Property(str, notify=stateChanged)
    def delimiter(self) -> str:
        return self._identity("delimiter")

    @Property(str, notify=stateChanged)
    def encoding(self) -> str:
        return self._identity("encoding")

    @Property(str, notify=stateChanged)
    def lastModified(self) -> str:  # noqa: N802
        return self._identity("last_modified")

    @Property(str, notify=stateChanged)
    def packageName(self) -> str:  # noqa: N802
        return self._package.display_name if self._package else "Production Model not configured"

    @Property(str, notify=stateChanged)
    def packageVersion(self) -> str:  # noqa: N802
        return self._package.version if self._package else "—"

    @Property(int, notify=stateChanged)
    def requiredCount(self) -> int:  # noqa: N802
        fit = self._session.fit
        return fit.required_count if fit else 0

    @Property(int, notify=stateChanged)
    def availableRequiredCount(self) -> int:  # noqa: N802
        fit = self._session.fit
        return fit.available_required_count if fit else 0

    @Property(int, notify=stateChanged)
    def missingRequiredCount(self) -> int:  # noqa: N802
        fit = self._session.fit
        return len(fit.missing_required) if fit else 0

    @Property(int, notify=stateChanged)
    def missingOmissibleCount(self) -> int:  # noqa: N802
        fit = self._session.fit
        return len(fit.missing_omissible) if fit else 0

    @Property(int, notify=stateChanged)
    def surplusCount(self) -> int:  # noqa: N802
        fit = self._session.fit
        return len(fit.surplus_columns) if fit else 0

    @Property(int, notify=stateChanged)
    def blockingCount(self) -> int:  # noqa: N802
        if self._session.source and self._package is None:
            return 1
        fit = self._session.fit
        return len(fit.blocking_issues) if fit else 0

    @Property(int, notify=stateChanged)
    def warningCount(self) -> int:  # noqa: N802
        fit = self._session.fit
        return len(fit.warnings) if fit else 0

    @Property(str, notify=stateChanged)
    def contractStatus(self) -> str:  # noqa: N802
        if not self._session.source:
            return "Awaiting source"
        if not self._package:
            return "Model Package required"
        fit = self._session.fit
        if fit and fit.blocking_issues:
            return f"{len(fit.blocking_issues)} blocking issue(s)"
        if fit and fit.warnings:
            return f"Compatible · {len(fit.warnings)} warning(s)"
        return "No blocking issues"

    @Property(str, notify=stateChanged)
    def contractDetail(self) -> str:  # noqa: N802
        if self._package_error:
            return self._package_error
        fit = self._session.fit
        if fit and fit.blocking_issues:
            return " · ".join(finding.message for finding in fit.blocking_issues)
        if fit and fit.warnings:
            return " · ".join(finding.message for finding in fit.warnings)
        return "Contract policy is read from the validated Model Package."

    @Property(str, notify=stateChanged)
    def typeHandling(self) -> str:  # noqa: N802
        return self._audit("type_handling", "Awaiting contract")

    @Property(str, notify=stateChanged)
    def missingValueHandling(self) -> str:  # noqa: N802
        return self._audit("missing_values", "Awaiting contract")

    @Property(str, notify=stateChanged)
    def categoryMapping(self) -> str:  # noqa: N802
        return self._audit("category_mapping", "Awaiting contract")

    @Property(str, notify=stateChanged)
    def columnMapping(self) -> str:  # noqa: N802
        return self._audit("column_mapping", "Awaiting contract")

    @Property(str, notify=stateChanged)
    def rowFiltering(self) -> str:  # noqa: N802
        return self._audit("row_filtering", "None")

    @Property(bool, notify=stateChanged)
    def canConfirm(self) -> bool:  # noqa: N802
        return self._session.can_confirm

    @Property(bool, notify=stateChanged)
    def confirmed(self) -> bool:
        return self._session.operator_confirmed

    @Property(bool, notify=stateChanged)
    def runEnabled(self) -> bool:  # noqa: N802
        return self._session.run_enabled

    @Property(str, notify=stateChanged)
    def runButtonText(self) -> str:  # noqa: N802
        if not self._session.source:
            return "Open a CSV to continue"
        if not self._session.can_confirm:
            return "Resolve blocking issues"
        if not self._session.operator_confirmed:
            return "Confirm the reviewed source"
        return "Confirm source & request prediction"

    @Property(str, notify=stateChanged)
    def statusMessage(self) -> str:  # noqa: N802
        return self._status_message

    @Property(str, notify=stateChanged)
    def statusKind(self) -> str:  # noqa: N802
        return self._status_kind

    @Property(str, constant=True)
    def identityReferenceUrl(self) -> str:  # noqa: N802
        return QUrl.fromLocalFile(str(self._identity_reference)).toString() if self._identity_reference else ""

    @Slot(str)
    def openSource(self, value: str) -> None:  # noqa: N802
        url = QUrl(value)
        path = Path(url.toLocalFile() if url.isLocalFile() else value)
        try:
            source = self._reader.open(path)
            self._session.load_source(source, self._package)
            self._table_model.set_source(source)
            self._status_message = "Source ready for review."
            self._status_kind = "success" if self._session.can_confirm else "warning"
        except (CsvSourceError, OSError, ValueError) as error:
            self._status_message = str(error)
            self._status_kind = "error"
        self._emit()

    @Slot(bool)
    def setConfirmed(self, confirmed: bool) -> None:  # noqa: N802
        self._session.set_operator_confirmation(confirmed and self._session.can_confirm)
        self._emit()

    @Slot(str)
    def filterColumns(self, query: str) -> None:  # noqa: N802
        self._table_model.filter_columns(query)

    @Slot()
    def resetColumns(self) -> None:  # noqa: N802
        self._table_model.reset_columns()

    @Slot()
    def requestRun(self) -> None:  # noqa: N802
        if not self._session.run_enabled:
            return
        self._status_message = (
            "Source confirmation recorded. The deterministic inference adapter is the next milestone."
        )
        self._status_kind = "success"
        self._emit()

    @Slot()
    def close(self) -> None:
        self._session.close()

    def _identity(self, name: str) -> str:
        source = self._session.source
        return str(getattr(source.identity, name)) if source else "—"

    def _audit(self, topic: str, default: str) -> str:
        audit = self._session.audit
        return audit.summary_for(topic, default) if audit else default

