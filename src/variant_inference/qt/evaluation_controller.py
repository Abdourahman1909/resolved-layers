from __future__ import annotations

from concurrent.futures import Executor, Future, ThreadPoolExecutor

from PySide6.QtCore import Property, QObject, Signal, Slot

from variant_inference.application.ports import EvaluationService
from variant_inference.domain.models import (
    EvaluationReport,
    EvaluationSourceEvidence,
    GroundTruthAuthorization,
    LabelCoverage,
    LoadedVerifiedRun,
    SourceReferenceState,
)
from variant_inference.qt.evaluation_models import (
    EvaluationCohortModel,
    EvaluationGroupModel,
    EvaluationMetricModel,
)


class EvaluationController(QObject):
    stateChanged = Signal()
    operationFinished = Signal(int, str, object, str)

    def __init__(
        self,
        service: EvaluationService,
        metrics: EvaluationMetricModel,
        cohorts: EvaluationCohortModel,
        executor: Executor | None = None,
        *,
        groups: EvaluationGroupModel | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._metrics = metrics
        self._cohorts = cohorts
        self._groups = groups
        self._owns_executor = executor is None
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="resolved-layers-evaluation",
        )
        self._request_id = 0
        self._busy = False
        self._busy_message = ""
        self._run: LoadedVerifiedRun | None = None
        self._source = EvaluationSourceEvidence(
            SourceReferenceState.MISSING,
            "",
            detail="Open a Verified Run to prepare Evaluation.",
        )
        self._selected_label_column = ""
        self._label_values: tuple[str, ...] = ()
        self._authorization: GroundTruthAuthorization | None = None
        self._draft_pathogenic = ""
        self._draft_benign = ""
        self._preview: LabelCoverage | None = None
        self._report: EvaluationReport | None = None
        # Grouping is opt-in. Nothing is grouped until the operator asks,
        # consistent with the workspace never choosing a column on its own.
        self._group_column = ""
        self._message = "Open a Verified Run to prepare Evaluation."
        self._error_message = ""
        self.operationFinished.connect(self._apply_operation)

    def load_run(self, run: LoadedVerifiedRun) -> None:
        self._run = run
        self._clear_authorization()
        self.refreshSource()

    @Property(bool, notify=stateChanged)
    def hasRun(self) -> bool:  # noqa: N802
        return self._run is not None

    @Property(str, notify=stateChanged)
    def sourceState(self) -> str:  # noqa: N802
        return self._source.state.value

    @Property(bool, notify=stateChanged)
    def sourceAvailable(self) -> bool:  # noqa: N802
        return self._source.is_available

    @Property(str, notify=stateChanged)
    def sourceDetail(self) -> str:  # noqa: N802
        return self._source.detail

    @Property(str, notify=stateChanged)
    def expectedSha256(self) -> str:  # noqa: N802
        return self._source.expected_sha256

    @Property(str, notify=stateChanged)
    def currentSha256(self) -> str:  # noqa: N802
        return self._source.current_sha256

    @Property("QStringList", notify=stateChanged)
    def labelColumns(self) -> list[str]:  # noqa: N802
        return list(self._source.label_columns)

    @Property(str, notify=stateChanged)
    def selectedLabelColumn(self) -> str:  # noqa: N802
        return self._selected_label_column

    # Group breakdown --------------------------------------------------------

    @Property("QStringList", notify=stateChanged)
    def groupColumns(self) -> list[str]:  # noqa: N802
        """Columns offered for grouping, excluding the authorized label column.

        Grouping by the label column would only restate the confusion matrix.
        """
        return [
            column
            for column in self._source.label_columns
            if column != self._selected_label_column
        ]

    @Property(str, notify=stateChanged)
    def groupColumn(self) -> str:  # noqa: N802
        return self._group_column

    @Property(bool, notify=stateChanged)
    def hasGrouping(self) -> bool:  # noqa: N802
        report = self._report
        return bool(report and report.grouping and report.grouping.groups)

    @Property(int, notify=stateChanged)
    def groupCount(self) -> int:  # noqa: N802
        report = self._report
        return len(report.grouping.groups) if report and report.grouping else 0

    @Property(str, notify=stateChanged)
    def meanGroupF1(self) -> str:  # noqa: N802
        """Unweighted mean across groups — each group counted equally."""
        report = self._report
        return report.grouping.mean_display("f1") if report and report.grouping else "—"

    @Property(str, notify=stateChanged)
    def meanGroupMcc(self) -> str:  # noqa: N802
        report = self._report
        return report.grouping.mean_display("mcc") if report and report.grouping else "—"

    @Slot(str)
    def selectGroupColumn(self, column_name: str) -> None:  # noqa: N802
        """Choose a grouping column, or pass an empty string to stop grouping.

        Re-runs the evaluation, because grouping reads source values and that
        work belongs off the QML thread like every other source read.
        """
        if self._busy:
            return
        if column_name and column_name not in self._source.label_columns:
            self._error_message = f"{column_name!r} is not an available source column."
            self.stateChanged.emit()
            return
        if column_name == self._group_column:
            return
        self._group_column = column_name
        if self._authorization is None or self._run is None:
            self.stateChanged.emit()
            return
        self._schedule(
            "evaluate",
            self._evaluate_mapping,
            self._run,
            self._authorization,
            busy_message=(
                f"Grouping observed metrics by {column_name}…"
                if column_name
                else "Removing the group breakdown…"
            ),
        )

    @Property("QStringList", notify=stateChanged)
    def labelValues(self) -> list[str]:  # noqa: N802
        return list(self._label_values)

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def busyMessage(self) -> str:  # noqa: N802
        return self._busy_message

    @Property(bool, notify=stateChanged)
    def evaluationAuthorized(self) -> bool:  # noqa: N802
        return self._authorization is not None and self._report is not None and not self._busy

    @Property(bool, notify=stateChanged)
    def hasReport(self) -> bool:  # noqa: N802
        return self._report is not None and not self._busy

    @Property(bool, notify=stateChanged)
    def hasCoveragePreview(self) -> bool:  # noqa: N802
        return self._preview is not None and not self._busy

    @Property(str, notify=stateChanged)
    def pathogenicMapping(self) -> str:  # noqa: N802
        return self._draft_pathogenic

    @Property(str, notify=stateChanged)
    def benignMapping(self) -> str:  # noqa: N802
        return self._draft_benign

    @Property(int, notify=stateChanged)
    def previewTotalCount(self) -> int:  # noqa: N802
        return self._preview.total if self._preview else 0

    @Property(int, notify=stateChanged)
    def previewEvaluatedCount(self) -> int:  # noqa: N802
        return self._preview.recognized if self._preview else 0

    @Property(int, notify=stateChanged)
    def previewMissingCount(self) -> int:  # noqa: N802
        return self._preview.missing if self._preview else 0

    @Property(int, notify=stateChanged)
    def previewUnrecognizedCount(self) -> int:  # noqa: N802
        return self._preview.unrecognized if self._preview else 0

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def errorMessage(self) -> str:  # noqa: N802
        return self._error_message

    @Property(int, notify=stateChanged)
    def totalCount(self) -> int:  # noqa: N802
        return self._report.total_records if self._report else 0

    @Property(int, notify=stateChanged)
    def evaluatedCount(self) -> int:  # noqa: N802
        return self._report.evaluated_count if self._report else 0

    @Property(int, notify=stateChanged)
    def excludedCount(self) -> int:  # noqa: N802
        return self._report.excluded_count if self._report else 0

    @Property(int, notify=stateChanged)
    def missingCount(self) -> int:  # noqa: N802
        return self._report.missing_count if self._report else 0

    @Property(int, notify=stateChanged)
    def unrecognizedCount(self) -> int:  # noqa: N802
        return self._report.unrecognized_count if self._report else 0

    @Property(int, notify=stateChanged)
    def truePositive(self) -> int:  # noqa: N802
        return self._report.true_positive if self._report else 0

    @Property(int, notify=stateChanged)
    def falsePositive(self) -> int:  # noqa: N802
        return self._report.false_positive if self._report else 0

    @Property(int, notify=stateChanged)
    def falseNegative(self) -> int:  # noqa: N802
        return self._report.false_negative if self._report else 0

    @Property(int, notify=stateChanged)
    def trueNegative(self) -> int:  # noqa: N802
        return self._report.true_negative if self._report else 0

    @Slot()
    def refreshSource(self) -> None:  # noqa: N802
        if self._run is None:
            return
        self._schedule(
            "prepare",
            self._service.prepare,
            self._run,
            busy_message="Verifying the original Source Dataset…",
        )

    @Slot(str)
    def selectLabelColumn(self, column_name: str) -> None:  # noqa: N802
        if not self._run or not self._source.is_available or self._busy:
            return
        if column_name and column_name not in self._source.label_columns:
            self._error_message = f"{column_name!r} is not an available source column."
            self.stateChanged.emit()
            return
        self._selected_label_column = column_name
        self._clear_authorization(keep_column=True)
        if not column_name:
            self._message = (
                "Select a label column; no column is inferred automatically."
            )
            self._error_message = ""
            self.stateChanged.emit()
            return
        self._schedule(
            "label_values",
            self._load_label_values,
            self._run,
            column_name,
            busy_message="Reading exact raw values…",
        )

    @Slot(str, str)
    def reviewCoverage(self, pathogenic_value: str, benign_value: str) -> None:  # noqa: N802
        self._request_id += 1
        self._busy = False
        self._busy_message = ""
        self._draft_pathogenic = pathogenic_value
        self._draft_benign = benign_value
        self._preview = None
        self._authorization = None
        self._report = None
        if self._groups is not None:
            self._groups.set_items(())
        self._metrics.set_items(())
        self._cohorts.set_items(())
        if self._run is None or not self._selected_label_column:
            self._error_message = "Select the label column before reviewing coverage."
            self._message = self._error_message
            self.stateChanged.emit()
            return
        if not pathogenic_value or not benign_value or pathogenic_value == benign_value:
            self._error_message = ""
            self._message = "Choose two different exact raw values to review label coverage."
            self.stateChanged.emit()
            return
        proposed_mapping = GroundTruthAuthorization(
            self._selected_label_column,
            pathogenic_value,
            benign_value,
        )
        self._schedule(
            "preview",
            self._preview_mapping,
            self._run,
            proposed_mapping,
            busy_message="Verifying proposed label coverage…",
        )

    @Slot(str, str)
    def authorizeEvaluation(self, pathogenic_value: str, benign_value: str) -> None:  # noqa: N802
        if self._run is None or not self._selected_label_column or self._busy:
            self._error_message = "Select the label column before authorizing Evaluation."
            self.stateChanged.emit()
            return
        if (
            self._preview is None
            or pathogenic_value != self._draft_pathogenic
            or benign_value != self._draft_benign
        ):
            self._error_message = (
                "Review valid, missing, and unrecognized counts before authorizing Evaluation."
            )
            self._message = self._error_message
            self.stateChanged.emit()
            return
        authorization = GroundTruthAuthorization(
            self._selected_label_column,
            pathogenic_value,
            benign_value,
        )
        self._schedule(
            "evaluate",
            self._evaluate_mapping,
            self._run,
            authorization,
            busy_message="Calculating observed Evaluation…",
        )

    @Slot()
    def clearAuthorization(self) -> None:  # noqa: N802
        self._request_id += 1
        self._busy = False
        self._busy_message = ""
        self._clear_authorization(keep_column=True)
        self._message = "Evaluation authorization cleared; no observed metrics are active."
        self._error_message = ""
        self.stateChanged.emit()

    def cohort_source_rows(self, key: str) -> tuple[int, ...]:
        if self._report is None:
            return ()
        return self._report.cohort(key).source_rows

    def cohort_title(self, key: str) -> str:
        if self._report is None:
            return "Evaluation cohort"
        return self._report.cohort(key).title

    def _clear_authorization(self, keep_column: bool = False) -> None:
        if not keep_column:
            self._selected_label_column = ""
            self._label_values = ()
        self._authorization = None
        self._draft_pathogenic = ""
        self._draft_benign = ""
        self._preview = None
        self._report = None
        if self._groups is not None:
            self._groups.set_items(())
        self._metrics.set_items(())
        self._cohorts.set_items(())

    def close(self) -> None:
        self._request_id += 1
        if self._owns_executor:
            self._executor.shutdown(wait=True, cancel_futures=True)

    def _schedule(self, operation: str, function, *args, busy_message: str) -> None:
        self._request_id += 1
        request_id = self._request_id
        self._busy = True
        self._busy_message = busy_message
        self._error_message = ""
        self.stateChanged.emit()
        future = self._executor.submit(function, *args)
        future.add_done_callback(
            lambda completed, request=request_id, kind=operation: self._queue_operation(
                request, kind, completed
            )
        )

    def _queue_operation(self, request_id: int, operation: str, future: Future) -> None:
        try:
            result = future.result()
            error_message = ""
        except Exception as error:  # Surface archive, source, and validation failures fail-closed.
            result = None
            error_message = str(error)
        self.operationFinished.emit(request_id, operation, result, error_message)

    @Slot(int, str, object, str)
    def _apply_operation(
        self, request_id: int, operation: str, result: object, error_message: str
    ) -> None:
        if request_id != self._request_id:
            return
        self._busy = False
        self._busy_message = ""
        if error_message:
            self._clear_authorization(keep_column=True)
            self._error_message = error_message
            self._message = error_message
            if operation in {"prepare", "recover"}:
                expected = self._run.source_sha256 if self._run else ""
                self._source = EvaluationSourceEvidence(
                    SourceReferenceState.MISSING,
                    expected,
                    detail=error_message,
                )
                self.stateChanged.emit()
            elif self._run is not None:
                self._schedule(
                    "recover",
                    self._service.prepare,
                    self._run,
                    busy_message="Revalidating source evidence after the failed request…",
                )
                self._error_message = error_message
                self._message = error_message
            return

        if operation in {"prepare", "recover"}:
            assert isinstance(result, EvaluationSourceEvidence)
            self._source = result
            if not result.is_available:
                self._clear_authorization()
                self._message = result.detail
            elif self._report is None:
                self._message = "Select a label column and authorize both exact raw mappings."
            if operation == "prepare":
                self._error_message = ""
        elif operation == "label_values":
            column_name, values = result
            if column_name != self._selected_label_column:
                return
            self._label_values = values
            self._message = (
                "Map both exact raw values, review coverage, then authorize Evaluation."
            )
            self._error_message = ""
        elif operation == "preview":
            mapping, coverage = result
            self._authorization = None
            self._report = None
            self._metrics.set_items(())
            self._cohorts.set_items(())
            self._draft_pathogenic = mapping.pathogenic_value
            self._draft_benign = mapping.benign_value
            self._preview = coverage
            self._message = (
                f"Review coverage: {coverage.recognized:,} of {coverage.total:,} labels are valid; "
                f"{coverage.missing:,} missing and {coverage.unrecognized:,} unrecognized."
            )
            self._error_message = ""
        elif operation == "evaluate":
            authorization, report = result
            self._authorization = authorization
            self._report = report
            self._metrics.set_items(report.metrics)
            self._cohorts.set_items(report.cohorts)
            if self._groups is not None:
                self._groups.set_items(
                    report.grouping.groups if report.grouping else ()
                )
            self._message = (
                f"Observed Evaluation authorized for {report.evaluated_count:,} of "
                f"{report.total_records:,} Source Rows."
            )
            self._error_message = ""
        self.stateChanged.emit()

    def _load_label_values(
        self, run: LoadedVerifiedRun, column_name: str
    ) -> tuple[str, tuple[str, ...]]:
        return column_name, self._service.label_values(run, column_name)

    def _preview_mapping(
        self, run: LoadedVerifiedRun, mapping: GroundTruthAuthorization
    ) -> tuple[GroundTruthAuthorization, LabelCoverage]:
        return mapping, self._service.preview(run, mapping)

    def _evaluate_mapping(
        self, run: LoadedVerifiedRun, authorization: GroundTruthAuthorization
    ) -> tuple[GroundTruthAuthorization, EvaluationReport]:
        return authorization, self._service.evaluate(
            run, authorization, group_by=self._group_column or None
        )
