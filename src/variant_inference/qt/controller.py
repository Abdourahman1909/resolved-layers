from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from variant_inference.application.dataset_profile import DatasetProfileSession
from variant_inference.application.source_review import SourceReviewSession
from variant_inference.application.verified_run import VerifiedRunService
from variant_inference.domain.models import ModelPackageIdentity
from variant_inference.infrastructure.csv_source import CsvSourceError, CsvSourceReader
from variant_inference.qt.table_model import CsvTableModel
from variant_inference.qt.profile_model import GroupBreakdownModel
from variant_inference.qt.results_controller import ResultsController
from variant_inference.qt.evaluation_controller import EvaluationController


class SourceReviewController(QObject):
    stateChanged = Signal()

    def __init__(
        self,
        table_model: CsvTableModel,
        group_model: GroupBreakdownModel,
        package: ModelPackageIdentity | None,
        package_error: str = "",
        identity_lockup: Path | None = None,
        verified_runs: VerifiedRunService | None = None,
        run_unavailable_reason: str = "",
        results_controller: ResultsController | None = None,
        evaluation_controller: EvaluationController | None = None,
    ) -> None:
        super().__init__()
        self._table_model = table_model
        self._group_model = group_model
        self._reader = CsvSourceReader()
        self._session = SourceReviewSession(package=package)
        self._profile = DatasetProfileSession()
        self._package = package
        self._package_error = package_error
        self._verified_runs = verified_runs
        self._run_unavailable_reason = run_unavailable_reason
        self._results_controller = results_controller
        self._evaluation_controller = evaluation_controller
        self._last_run_id = ""
        self._last_run_path = ""
        self._status_message = "Open a Source Dataset to begin review."
        self._status_kind = "neutral"
        self._identity_lockup = identity_lockup
        self._active_surface = "review"
        self._profile_message = "Select a label column and map both classes explicitly."

    def _emit(self) -> None:
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def hasSource(self) -> bool:  # noqa: N802
        return self._session.source is not None

    @Property(str, notify=stateChanged)
    def activeSurface(self) -> str:  # noqa: N802
        return self._active_surface

    @Property(bool, notify=stateChanged)
    def hasResults(self) -> bool:  # noqa: N802
        return bool(self._results_controller and self._results_controller.hasRun)

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

    @Property(int, notify=stateChanged)
    def missingCellCount(self) -> int:  # noqa: N802
        source = self._session.source
        return getattr(source, "missing_cell_count", 0) if source else 0

    @Property(int, notify=stateChanged)
    def rowsWithMissing(self) -> int:  # noqa: N802
        source = self._session.source
        return getattr(source, "rows_with_missing", 0) if source else 0

    @Property("QStringList", notify=stateChanged)
    def groupColumns(self) -> list[str]:  # noqa: N802
        return list(self._profile.group_columns)

    @Property(str, notify=stateChanged)
    def groupColumn(self) -> str:  # noqa: N802
        return self._profile.group_column

    @Property(int, notify=stateChanged)
    def groupCount(self) -> int:  # noqa: N802
        return len(self._profile.groups)

    @Property("QStringList", notify=stateChanged)
    def labelColumns(self) -> list[str]:  # noqa: N802
        return list(self._profile.label_columns)

    @Property(str, notify=stateChanged)
    def selectedLabelColumn(self) -> str:  # noqa: N802
        return self._profile.label_column

    @Property("QStringList", notify=stateChanged)
    def labelValues(self) -> list[str]:  # noqa: N802
        return list(self._profile.label_values)

    @Property(bool, notify=stateChanged)
    def labelsAuthorized(self) -> bool:  # noqa: N802
        return self._profile.authorization is not None

    @Property(str, notify=stateChanged)
    def authorizedLabelColumn(self) -> str:  # noqa: N802
        authorization = self._profile.authorization
        return authorization.column_name if authorization else ""

    @Property(str, notify=stateChanged)
    def pathogenicMapping(self) -> str:  # noqa: N802
        authorization = self._profile.authorization
        return authorization.pathogenic_value if authorization else ""

    @Property(str, notify=stateChanged)
    def benignMapping(self) -> str:  # noqa: N802
        authorization = self._profile.authorization
        return authorization.benign_value if authorization else ""

    @Property(int, notify=stateChanged)
    def pathogenicCount(self) -> int:  # noqa: N802
        coverage = self._profile.label_coverage
        return coverage.pathogenic if coverage else 0

    @Property(int, notify=stateChanged)
    def benignCount(self) -> int:  # noqa: N802
        coverage = self._profile.label_coverage
        return coverage.benign if coverage else 0

    @Property(int, notify=stateChanged)
    def missingLabelCount(self) -> int:  # noqa: N802
        coverage = self._profile.label_coverage
        return coverage.missing if coverage else 0

    @Property(int, notify=stateChanged)
    def unrecognizedLabelCount(self) -> int:  # noqa: N802
        coverage = self._profile.label_coverage
        return coverage.unrecognized if coverage else 0

    @Property(int, notify=stateChanged)
    def recognizedLabelCount(self) -> int:  # noqa: N802
        coverage = self._profile.label_coverage
        return coverage.recognized if coverage else 0

    @Property(float, notify=stateChanged)
    def pathogenicShare(self) -> float:  # noqa: N802
        coverage = self._profile.label_coverage
        return (coverage.pathogenic / coverage.recognized) if coverage and coverage.recognized else 0.0

    @Property(str, notify=stateChanged)
    def labelCoverageText(self) -> str:  # noqa: N802
        coverage = self._profile.label_coverage
        if coverage is None:
            return "Class composition unavailable"
        return f"{coverage.recognized:,} of {coverage.total:,} labels recognized"

    @Property(str, notify=stateChanged)
    def profileMessage(self) -> str:  # noqa: N802
        return self._profile_message

    @Property(str, notify=stateChanged)
    def classFilter(self) -> str:  # noqa: N802
        return self._profile.class_filter

    @Property(bool, notify=stateChanged)
    def hasGroupFilter(self) -> bool:  # noqa: N802
        return self._profile.group_filter is not None

    @Property(str, notify=stateChanged)
    def groupFilterValue(self) -> str:  # noqa: N802
        return self._profile.group_filter or "" if self._profile.group_filter is not None else ""

    @Property(str, notify=stateChanged)
    def groupFilterDisplay(self) -> str:  # noqa: N802
        if self._profile.group_filter is None:
            return ""
        value = self._profile.group_filter or "Missing"
        return f"{self._profile.group_column}: {value}"

    @Property(int, notify=stateChanged)
    def activeFilterCount(self) -> int:  # noqa: N802
        return len(self._profile.active_filters)

    @Property(int, notify=stateChanged)
    def filteredRowCount(self) -> int:  # noqa: N802
        return self._table_model.filtered_row_count

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
        return self._session.run_enabled and self._verified_runs is not None

    @Property(str, notify=stateChanged)
    def runButtonText(self) -> str:  # noqa: N802
        if not self._session.source:
            return "Open a CSV to continue"
        if self._package is None:
            # Without a Model Package there is no Inference Contract to fit, so
            # the source cannot be confirmed. Name the real cause instead of
            # blaming the reviewed source for blocking issues it does not have.
            return self._run_unavailable_reason or "No Model Package installed"
        if not self._session.can_confirm:
            return "Resolve blocking issues"
        if not self._session.operator_confirmed:
            return "Confirm the reviewed source"
        if self._verified_runs is None:
            return self._run_unavailable_reason or "Trusted inference unavailable"
        return "Create immutable Verified Run"

    @Property(str, notify=stateChanged)
    def lastRunId(self) -> str:  # noqa: N802
        return self._last_run_id

    @Property(str, notify=stateChanged)
    def lastRunPath(self) -> str:  # noqa: N802
        return self._last_run_path

    @Property(str, notify=stateChanged)
    def statusMessage(self) -> str:  # noqa: N802
        return self._status_message

    @Property(str, notify=stateChanged)
    def statusKind(self) -> str:  # noqa: N802
        return self._status_kind

    @Property(str, constant=True)
    def identityLockupUrl(self) -> str:  # noqa: N802
        return QUrl.fromLocalFile(str(self._identity_lockup)).toString() if self._identity_lockup else ""

    @Slot(str)
    def openSource(self, value: str) -> None:  # noqa: N802
        url = QUrl(value)
        path = Path(url.toLocalFile() if url.isLocalFile() else value)
        try:
            source = self._reader.open(path)
            self._last_run_id = ""
            self._last_run_path = ""
            self._session.load_source(source, self._package)
            self._table_model.set_source(source)
            context_columns = list(source.columns)
            if self._session.fit is not None:
                context_columns = list(self._session.fit.surplus_columns)
                if "_panel" in source.columns and "_panel" not in context_columns:
                    context_columns.insert(0, "_panel")
            self._profile.load_source(source, context_columns)
            self._refresh_profile()
            self._status_message = "Source ready for review."
            self._status_kind = "success" if self._session.can_confirm else "warning"
        except (CsvSourceError, OSError, ValueError) as error:
            self._status_message = str(error)
            self._status_kind = "error"
        self._emit()

    @Slot(str)
    def setActiveSurface(self, surface: str) -> None:  # noqa: N802
        if surface not in {"review", "profile", "results", "evaluation"}:
            return
        if surface == "profile" and not self.hasSource:
            return
        if surface == "results" and not self.hasResults:
            return
        if surface == "evaluation" and not self.hasResults:
            return
        if surface == "evaluation" and self._evaluation_controller is not None:
            self._evaluation_controller.refreshSource()
        self._active_surface = surface
        self._table_model.set_row_filter(
            self._profile.filtered_source_rows if surface == "profile" else None
        )
        self._emit()

    @Slot(str)
    def selectGroupColumn(self, column_name: str) -> None:  # noqa: N802
        try:
            self._profile.select_group_column(column_name)
            self._refresh_profile()
        except ValueError as error:
            self._profile_message = str(error)
        self._emit()

    @Slot(str)
    def selectLabelColumn(self, column_name: str) -> None:  # noqa: N802
        try:
            self._profile.select_label_column(column_name)
            self._profile_message = "Map one source value to each class, then authorize the mapping."
            self._refresh_profile()
        except ValueError as error:
            self._profile_message = str(error)
        self._emit()

    @Slot(str, str)
    def authorizeLabels(self, pathogenic_value: str, benign_value: str) -> None:  # noqa: N802
        try:
            self._profile.authorize_labels(pathogenic_value, benign_value)
            coverage = self._profile.label_coverage
            assert coverage is not None
            self._profile_message = (
                f"Authorized {coverage.recognized:,} labels; {coverage.missing:,} missing and "
                f"{coverage.unrecognized:,} unrecognized remain outside the mapping."
            )
            self._refresh_profile()
        except ValueError as error:
            self._profile_message = str(error)
        self._emit()

    @Slot()
    def clearLabelAuthorization(self) -> None:  # noqa: N802
        self._profile.clear_authorization()
        self._profile_message = "Label authorization cleared. Class composition is unavailable."
        self._refresh_profile()
        self._emit()

    @Slot(str)
    def setClassFilter(self, class_name: str) -> None:  # noqa: N802
        try:
            self._profile.set_class_filter("" if self._profile.class_filter == class_name else class_name)
            self._refresh_profile()
        except ValueError as error:
            self._profile_message = str(error)
        self._emit()

    @Slot(str)
    def setGroupFilter(self, value: str) -> None:  # noqa: N802
        next_value = None if self._profile.group_filter == value else value
        self._profile.set_group_filter(next_value)
        self._refresh_profile()
        self._emit()

    @Slot()
    def clearGroupFilter(self) -> None:  # noqa: N802
        self._profile.set_group_filter(None)
        self._refresh_profile()
        self._emit()

    @Slot()
    def clearProfileFilters(self) -> None:  # noqa: N802
        self._profile.set_class_filter("")
        self._profile.set_group_filter(None)
        self._refresh_profile()
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
        if not self._session.run_enabled or self._verified_runs is None:
            return
        assert self._session.source is not None
        assert self._session.package is not None
        assert self._session.fit is not None
        assert self._session.audit is not None
        try:
            archived = self._verified_runs.execute(
                source=self._session.source,
                package=self._session.package,
                fit=self._session.fit,
                audit=self._session.audit,
                operator_confirmed=self._session.operator_confirmed,
            )
            self._last_run_id = archived.run_id
            self._last_run_path = str(archived.directory)
            if self._results_controller is not None:
                self._results_controller.open_run(archived.run_id)
                if (
                    self._evaluation_controller is not None
                    and self._results_controller.current_run is not None
                ):
                    self._evaluation_controller.load_run(self._results_controller.current_run)
                self._active_surface = "results"
            self._status_message = f"Verified Run {archived.run_id} saved to the local Run Archive."
            self._status_kind = "success"
        except (OSError, RuntimeError, ValueError) as error:
            self._status_message = str(error)
            self._status_kind = "error"
        self._emit()

    @Slot(str, result=bool)
    def openArchivedRun(self, run_id: str) -> bool:  # noqa: N802
        if self._results_controller is None:
            return False
        opened = self._results_controller.open_run(run_id)
        if opened:
            if (
                self._evaluation_controller is not None
                and self._results_controller.current_run is not None
            ):
                self._evaluation_controller.load_run(self._results_controller.current_run)
            self._active_surface = "results"
            self._status_message = f"Verified Run {run_id} reopened from the local Run Archive."
            self._status_kind = "success"
        else:
            self._status_message = self._results_controller.errorMessage
            self._status_kind = "error"
        self._emit()
        return opened

    @Slot(str)
    def inspectEvaluationCohort(self, key: str) -> None:  # noqa: N802
        if self._evaluation_controller is None or self._results_controller is None:
            return
        source_rows = self._evaluation_controller.cohort_source_rows(key)
        if not source_rows:
            return
        title = f"Evaluation · {self._evaluation_controller.cohort_title(key)}"
        self._results_controller.showSourceRows(list(source_rows), title)
        self._active_surface = "results"
        self._emit()

    @Slot()
    def close(self) -> None:
        self._session.close()
        if self._results_controller is not None:
            self._results_controller.close()
        if self._evaluation_controller is not None:
            self._evaluation_controller.close()

    def _refresh_profile(self) -> None:
        self._group_model.set_groups(self._profile.groups, self._profile.authorization is not None)
        self._table_model.set_row_filter(
            self._profile.filtered_source_rows if self._active_surface == "profile" else None
        )

    def _identity(self, name: str) -> str:
        source = self._session.source
        return str(getattr(source.identity, name)) if source else "—"

    def _audit(self, topic: str, default: str) -> str:
        audit = self._session.audit
        return audit.summary_for(topic, default) if audit else default
