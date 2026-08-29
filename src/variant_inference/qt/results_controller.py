from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from variant_inference.application.results import ResultSetSession
from variant_inference.infrastructure.run_archive import DirectoryRunArchive, RunArchiveError
from variant_inference.qt.results_models import (
    InvestigationSetModel,
    PredictionTableModel,
    RunArchiveListModel,
    ScoreHistogramModel,
)


class ResultsController(QObject):
    stateChanged = Signal()

    def __init__(
        self,
        archive: DirectoryRunArchive,
        predictions: PredictionTableModel,
        histogram: ScoreHistogramModel,
        investigation_sets: InvestigationSetModel,
        archive_entries: RunArchiveListModel,
    ) -> None:
        super().__init__()
        self._archive = archive
        self._predictions = predictions
        self._histogram = histogram
        self._investigation_sets = investigation_sets
        self._archive_entries = archive_entries
        self._session = ResultSetSession()
        self._active_tab = "overview"
        self._source_state = "unknown"
        self._error_message = ""
        self.refreshArchive()

    @Property(bool, notify=stateChanged)
    def hasRun(self) -> bool:  # noqa: N802
        return self._session.run is not None

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

    @Slot()
    def refreshArchive(self) -> None:  # noqa: N802
        self._archive_entries.set_entries(self._archive.list_entries())
        self.stateChanged.emit()

    def open_run(self, run_id: str) -> bool:
        try:
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
        self._active_tab = "records"
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot()
    def showOverview(self) -> None:  # noqa: N802
        self._active_tab = "overview"
        self.stateChanged.emit()

    @Slot()
    def showRecords(self) -> None:  # noqa: N802
        self._session.clear_selection()
        self._active_tab = "records"
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot()
    def clearSelection(self) -> None:  # noqa: N802
        self._session.clear_selection()
        self._predictions.set_records(self._session.selected_records)
        self.stateChanged.emit()

    @Slot(str)
    def searchRecords(self, query: str) -> None:  # noqa: N802
        self._predictions.set_search(query)
        self.stateChanged.emit()

    def _sync_models(self) -> None:
        self._histogram.set_bins(self._session.score_bins)
        self._investigation_sets.set_items(self._session.investigation_sets)
        self._predictions.set_records(self._session.selected_records)

    def _value(self, name: str) -> str:
        run = self._session.run
        return str(getattr(run, name)) if run else ""
