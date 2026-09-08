from __future__ import annotations

from concurrent.futures import Executor, Future, ThreadPoolExecutor

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QAccessible, QAccessibleAnnouncementEvent

from variant_inference.application.results import ResultSetSession
from variant_inference.application.variant_inspector import (
    SourceRowEvidenceError,
    SourceRowEvidenceService,
)
from variant_inference.domain.models import PredictionRecord
from variant_inference.infrastructure.run_archive import DirectoryRunArchive, RunArchiveError
from variant_inference.qt.results_models import (
    InvestigationSetModel,
    PredictionTableModel,
    RunArchiveListModel,
    ScoreHistogramModel,
    SourceFieldListModel,
)


class ResultsController(QObject):
    stateChanged = Signal()
    sourceEvidenceFinished = Signal(int, object, str)

    def __init__(
        self,
        archive: DirectoryRunArchive,
        predictions: PredictionTableModel,
        histogram: ScoreHistogramModel,
        investigation_sets: InvestigationSetModel,
        archive_entries: RunArchiveListModel,
        source_evidence: SourceRowEvidenceService,
        source_fields: SourceFieldListModel,
        source_executor: Executor | None = None,
    ) -> None:
        super().__init__()
        self._archive = archive
        self._predictions = predictions
        self._histogram = histogram
        self._investigation_sets = investigation_sets
        self._archive_entries = archive_entries
        self._source_evidence = source_evidence
        self._source_fields = source_fields
        self._owns_source_executor = source_executor is None
        self._source_executor = source_executor or ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="resolved-layers-source-evidence",
        )
        self._source_request_id = 0
        self._session = ResultSetSession()
        self._active_tab = "overview"
        self._source_state = "unknown"
        self._error_message = ""
        self._selected_record: PredictionRecord | None = None
        self._selected_visible_row = -1
        self._source_evidence_state = "unavailable"
        self._source_evidence_detail = "Select a prediction record to inspect its evidence."
        self._source_expected_sha256 = ""
        self._source_current_sha256 = ""
        self.sourceEvidenceFinished.connect(self._apply_source_evidence)
        self.refreshArchive()

    @Property(bool, notify=stateChanged)
    def hasRun(self) -> bool:  # noqa: N802
        return self._session.run is not None

    @property
    def current_run(self):
        return self._session.run

    @Property(str, notify=stateChanged)
    def activeTab(self) -> str:  # noqa: N802
        return self._active_tab

    @Property(str, notify=stateChanged)
    def runId(self) -> str:  # noqa: N802
        return self._value("run_id")

    @Property(str, notify=stateChanged)
    def sourceName(self) -> str:  # noqa: N802
        return self._value("source_file_name")

    @Property(str, notify=stateChanged)
    def packageName(self) -> str:  # noqa: N802
        return self._value("model_package_name")

    @Property(str, notify=stateChanged)
    def packageVersion(self) -> str:  # noqa: N802
        return self._value("model_package_version")

    @Property(str, notify=stateChanged)
    def completedAt(self) -> str:  # noqa: N802
        return self._value("completed_at")

    @Property(int, notify=stateChanged)
    def durationMs(self) -> int:  # noqa: N802
        run = self._session.run
        return run.duration_ms if run else 0

    @Property(int, notify=stateChanged)
    def recordCount(self) -> int:  # noqa: N802
        return len(self._session.predictions)

    @Property(int, notify=stateChanged)
    def pathogenicCount(self) -> int:  # noqa: N802
        return self._session.pathogenic_count

    @Property(int, notify=stateChanged)
    def benignCount(self) -> int:  # noqa: N802
        return self._session.benign_count

    @Property(int, notify=stateChanged)
    def conflictCount(self) -> int:  # noqa: N802
        return self._session.component_conflict_count

    @Property(int, notify=stateChanged)
    def warningCount(self) -> int:  # noqa: N802
        run = self._session.run
        return len(run.warnings) if run else 0

    @Property(float, notify=stateChanged)
    def releaseThreshold(self) -> float:  # noqa: N802
        run = self._session.run
        return run.release_threshold if run else 0.0

    @Property(str, notify=stateChanged)
    def sourceState(self) -> str:  # noqa: N802
        return self._source_state

    @Property(str, notify=stateChanged)
    def errorMessage(self) -> str:  # noqa: N802
        return self._error_message

    @Property(str, notify=stateChanged)
    def selectionKey(self) -> str:  # noqa: N802
        return self._session.selection_key

    @Property(str, notify=stateChanged)
    def selectionTitle(self) -> str:  # noqa: N802
        return self._session.selection_title

    @Property(float, notify=stateChanged)
    def selectedLower(self) -> float:  # noqa: N802
        return self._session.selected_lower

    @Property(float, notify=stateChanged)
    def selectedUpper(self) -> float:  # noqa: N802
        return self._session.selected_upper

    @Property(int, notify=stateChanged)
    def selectedCount(self) -> int:  # noqa: N802
        return len(self._session.selected_records)

    @Property(int, notify=stateChanged)
    def visibleRecordCount(self) -> int:  # noqa: N802
        return self._predictions.visible_count

    @Property(int, notify=stateChanged)
    def archiveCount(self) -> int:  # noqa: N802
        return self._archive_entries.rowCount()

    @Property(bool, notify=stateChanged)
    def hasSelectedRecord(self) -> bool:  # noqa: N802
        return self._selected_record is not None

    @Property(int, notify=stateChanged)
    def selectedVisibleRow(self) -> int:  # noqa: N802
        return self._selected_visible_row

    @Property(int, notify=stateChanged)
    def selectedSourceRow(self) -> int:  # noqa: N802
        return self._selected_record.source_row if self._selected_record else 0

    @Property(str, notify=stateChanged)
    def selectedPrediction(self) -> str:  # noqa: N802
        return self._selected_record.prediction if self._selected_record else ""

    @Property(float, notify=stateChanged)
    def selectedEnsembleScore(self) -> float:  # noqa: N802
        return self._selected_record.ensemble_score if self._selected_record else 0.0

    @Property(float, notify=stateChanged)
    def selectedCatBoostScore(self) -> float:  # noqa: N802
        return self._component_score("catboost")

    @Property(float, notify=stateChanged)
    def selectedLightgbmScore(self) -> float:  # noqa: N802
        return self._component_score("lightgbm")

    @Property(float, notify=stateChanged)
    def selectedDisagreement(self) -> float:  # noqa: N802
        return self._selected_record.model_disagreement if self._selected_record else 0.0

    @Property(str, notify=stateChanged)
    def thresholdRelationship(self) -> str:  # noqa: N802
        if self._selected_record is None:
            return ""
        delta = self._selected_record.ensemble_score - self.releaseThreshold
        if abs(delta) < 5e-13:
            return "At Release Threshold"
        direction = "above" if delta > 0 else "below"
        return f"{abs(delta):.6f} {direction} threshold"

    @Property(str, notify=stateChanged)
    def sourceEvidenceState(self) -> str:  # noqa: N802
        return self._source_evidence_state

    @Property(str, notify=stateChanged)
    def sourceEvidenceDetail(self) -> str:  # noqa: N802
        return self._source_evidence_detail

    @Property(str, notify=stateChanged)
    def sourceExpectedSha256(self) -> str:  # noqa: N802
        return self._source_expected_sha256

    @Property(str, notify=stateChanged)
    def sourceCurrentSha256(self) -> str:  # noqa: N802
        return self._source_current_sha256

    @Property(int, notify=stateChanged)
    def sourceFieldCount(self) -> int:  # noqa: N802
        return self._source_fields.total_count

    @Property(int, notify=stateChanged)
    def visibleSourceFieldCount(self) -> int:  # noqa: N802
        return self._source_fields.rowCount()

    @Property(str, notify=stateChanged)
    def packageManifestChecksum(self) -> str:  # noqa: N802
        return self._value("model_package_manifest_checksum")

    @Property(str, notify=stateChanged)
    def contractId(self) -> str:  # noqa: N802
        return self._value("inference_contract_id")

    @Property(str, notify=stateChanged)
    def contractVersion(self) -> str:  # noqa: N802
        return self._value("inference_contract_version")

    @Property(str, notify=stateChanged)
    def contractChecksum(self) -> str:  # noqa: N802
        return self._value("inference_contract_checksum")

    @Slot()
    def refreshArchive(self) -> None:  # noqa: N802
        self._archive_entries.set_entries(self._archive.list_entries())
        self.stateChanged.emit()

    @Slot(str, result=bool)
    def deleteArchivedRun(self, run_id: str) -> bool:  # noqa: N802
        """Remove one archived run permanently.

        Not reversible, so the interface asks for a second, explicit action
        before calling this. If the removed run is the one on screen, the
        Results surface is cleared rather than left showing a run that no
        longer exists.
        """
        try:
            self._archive.delete(run_id)
        except Exception as error:  # surfaced, never swallowed
            self._error_message = str(error)
            self.stateChanged.emit()
            return False

        if self._session.run is not None and self._session.run.run_id == run_id:
            self._close_inspector()
            self._session.clear()
            self._source_state = "unknown"
            self._selected_record = None
            self._selected_visible_row = -1
            self._predictions.set_records(())
            self._histogram.set_bins(())
            self._investigation_sets.set_items(())
        self._error_message = ""
        self.refreshArchive()
        return True

    def open_run(self, run_id: str) -> bool:
        try:
            self._source_request_id += 1
            self._close_inspector()
            run = self._archive.load(run_id)
            self._session.load(run)
            self._source_state = self._archive.source_status(run_id).state.value
            self._active_tab = "overview"
            self._error_message = ""
            self._sync_models()
            self.refreshArchive()
            return True
        except (RunArchiveError, OSError, ValueError) as error:
            self._error_message = str(error)
            self.stateChanged.emit()
            return False

    @Slot(str)
    def selectInvestigationSet(self, key: str) -> None:  # noqa: N802
        self._session.select_investigation_set(key)
        self.stateChanged.emit()

    @Slot(float, float)
    def selectScoreRange(self, lower: float, upper: float) -> None:  # noqa: N802
        self._session.select_score_range(lower, upper)
        self.stateChanged.emit()

    @Slot()
    def inspectSelection(self) -> None:  # noqa: N802
        self._close_inspector()
        self._active_tab = "records"
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot()
    def showOverview(self) -> None:  # noqa: N802
        self._active_tab = "overview"
        self.stateChanged.emit()

    @Slot()
    def showRecords(self) -> None:  # noqa: N802
        self._close_inspector()
        self._session.clear_selection()
        self._active_tab = "records"
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot("QVariantList", str)
    def showSourceRows(self, source_rows: list[int], title: str) -> None:  # noqa: N802
        self._close_inspector()
        self._session.select_source_rows(tuple(int(value) for value in source_rows), title)
        self._active_tab = "records"
        self._predictions.set_search("")
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot()
    def clearSelection(self) -> None:  # noqa: N802
        self._close_inspector()
        self._session.clear_selection()
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot(str)
    def searchRecords(self, query: str) -> None:  # noqa: N802
        self._predictions.set_search(query)
        if self._selected_record is not None:
            visible_index = self._predictions.visible_index_for_source_row(
                self._selected_record.source_row
            )
            if visible_index < 0:
                self._close_inspector()
            else:
                self._selected_visible_row = visible_index
        self.stateChanged.emit()

    @Slot(int)
    def selectRecordAt(self, visible_row: int) -> None:  # noqa: N802
        run = self._session.run
        if run is None:
            return
        try:
            record = self._predictions.record_at(visible_row)
        except IndexError:
            return
        self._selected_record = record
        self._selected_visible_row = visible_row
        self._source_evidence_state = "checking"
        self._source_evidence_detail = "Verifying the original Source Dataset before reading row values."
        self._source_expected_sha256 = run.source_sha256
        self._source_current_sha256 = ""
        self._source_fields.set_fields(())
        self._source_request_id += 1
        request_id = self._source_request_id
        self.stateChanged.emit()
        self._announce(
            f"Source Row {record.source_row} selected. Variant Inspector opened."
        )
        future = self._source_executor.submit(
            self._source_evidence.read,
            run,
            record.source_row,
        )
        future.add_done_callback(
            lambda completed, request=request_id: self._queue_source_evidence(
                request, completed
            )
        )

    @Slot()
    def closeInspector(self) -> None:  # noqa: N802
        self._close_inspector()
        self.stateChanged.emit()

    @Slot(str)
    def searchSourceFields(self, query: str) -> None:  # noqa: N802
        self._source_fields.set_search(query)
        self.stateChanged.emit()

    @Slot()
    def close(self) -> None:
        self._source_request_id += 1
        future = self._source_executor.submit(self._source_evidence.close)
        if self._owns_source_executor:
            future.result(timeout=10)
            self._source_executor.shutdown(wait=True, cancel_futures=True)

    def _close_inspector(self) -> None:
        self._selected_record = None
        self._selected_visible_row = -1
        self._source_evidence_state = "unavailable"
        self._source_evidence_detail = "Select a prediction record to inspect its evidence."
        self._source_expected_sha256 = ""
        self._source_current_sha256 = ""
        self._source_fields.set_search("")
        self._source_fields.set_fields(())

    def _component_score(self, name: str) -> float:
        if self._selected_record is None:
            return 0.0
        return float(self._selected_record.component_scores.get(name, 0.0))

    def _queue_source_evidence(self, request_id: int, future: Future) -> None:
        try:
            evidence = future.result()
            error_message = ""
        except (OSError, RunArchiveError, SourceRowEvidenceError, ValueError) as error:
            evidence = None
            error_message = str(error)
        self.sourceEvidenceFinished.emit(request_id, evidence, error_message)

    @Slot(int, object, str)
    def _apply_source_evidence(
        self, request_id: int, evidence: object, error_message: str
    ) -> None:
        if request_id != self._source_request_id or self._selected_record is None:
            return
        if evidence is None:
            self._source_evidence_state = "unavailable"
            self._source_evidence_detail = error_message
            self._source_current_sha256 = ""
            self._source_fields.set_fields(())
        else:
            self._source_evidence_state = evidence.state.value
            self._source_evidence_detail = evidence.detail
            self._source_expected_sha256 = evidence.expected_sha256
            self._source_current_sha256 = evidence.current_sha256
            self._source_fields.set_fields(evidence.fields)
        self.stateChanged.emit()

    def _announce(self, message: str) -> None:
        try:
            QAccessible.updateAccessibility(QAccessibleAnnouncementEvent(self, message))
        except (RuntimeError, TypeError):
            pass

    def _sync_models(self) -> None:
        self._histogram.set_bins(self._session.score_bins)
        self._investigation_sets.set_items(self._session.investigation_sets)
        self._predictions.set_records(self._session.selected_records)

    def _value(self, name: str) -> str:
        run = self._session.run
        return str(getattr(run, name)) if run else ""
