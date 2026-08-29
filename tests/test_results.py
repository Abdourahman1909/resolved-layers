from __future__ import annotations

from pathlib import Path

from variant_inference.application.results import ResultSetSession
from variant_inference.domain.models import (
    LoadedVerifiedRun,
    PredictionRecord,
    RunArchiveEntry,
    SourceReferenceState,
    SourceReferenceStatus,
)
from variant_inference.qt.results_controller import ResultsController
from variant_inference.qt.results_models import (
    InvestigationSetModel,
    PredictionTableModel,
    RunArchiveListModel,
    ScoreHistogramModel,
)


def loaded_run() -> LoadedVerifiedRun:
    scores = (
        (0.20, 0.18, 0.22),
        (0.58, 0.52, 0.64),
        (0.62, 0.58, 0.66),
        (0.84, 0.82, 0.86),
    )
    predictions = tuple(
        PredictionRecord(
            source_row=index + 1,
            ensemble_score=ensemble,
            prediction="Pathogenic" if ensemble >= 0.61 else "Benign",
            component_scores={"catboost": catboost, "lightgbm": lightgbm},
            model_disagreement=abs(catboost - lightgbm) / 2,
        )
        for index, (ensemble, catboost, lightgbm) in enumerate(scores)
    )
    return LoadedVerifiedRun(
        run_id="run-results",
        created_at="2026-08-29T12:00:00+00:00",
        completed_at="2026-08-29T12:00:01+00:00",
        duration_ms=1000,
        source_path=Path("/tmp/source.csv"),
        source_file_name="source.csv",
        source_sha256="0" * 64,
        source_row_count=4,
        source_column_count=352,
        model_package_name="CHL Ensemble",
        model_package_version="2026.1",
        model_package_manifest_checksum="1" * 64,
        inference_contract_id="contract",
        inference_contract_version="2026.1",
        inference_contract_checksum="2" * 64,
        release_threshold=0.61,
        predictions_sha256="3" * 64,
        predictions=predictions,
    )


def test_result_session_builds_histogram_and_investigation_sets():
    session = ResultSetSession()
    session.load(loaded_run())

    assert sum(item.count for item in session.score_bins) == 4
    assert session.pathogenic_count == 2
    assert session.benign_count == 2
    assert session.component_conflict_count == 2
    assert [item.key for item in session.investigation_sets] == [
        "near_threshold",
        "component_conflict",
        "pathogenic",
        "benign",
    ]
    assert len(session.selected_records) == 2


def test_result_selection_moves_from_cohort_to_exact_records():
    session = ResultSetSession()
    session.load(loaded_run())

    session.select_investigation_set("component_conflict")
    assert [record.source_row for record in session.selected_records] == [2, 3]

    session.select_investigation_set("pathogenic")
    assert [record.source_row for record in session.selected_records] == [3, 4]

    session.select_score_range(0.80, 0.90)
    assert [record.source_row for record in session.selected_records] == [4]

    session.clear_selection()
    assert [record.source_row for record in session.selected_records] == [1, 2, 3, 4]


class MemoryArchive:
    def __init__(self, run: LoadedVerifiedRun) -> None:
        self.run = run

    def load(self, run_id: str) -> LoadedVerifiedRun:
        assert run_id == self.run.run_id
        return self.run

    def source_status(self, run_id: str) -> SourceReferenceStatus:
        assert run_id == self.run.run_id
        return SourceReferenceStatus(SourceReferenceState.AVAILABLE, self.run.source_sha256)

    def list_entries(self) -> tuple[RunArchiveEntry, ...]:
        return (
            RunArchiveEntry(
                run_id=self.run.run_id,
                completed_at=self.run.completed_at,
                source_file_name=self.run.source_file_name,
                model_package_name=self.run.model_package_name,
                model_package_version=self.run.model_package_version,
                record_count=len(self.run.predictions),
                pathogenic_count=2,
                warning_count=0,
            ),
        )


def test_results_controller_reopens_run_and_exposes_exact_selected_records():
    run = loaded_run()
    predictions = PredictionTableModel()
    controller = ResultsController(
        MemoryArchive(run),
        predictions,
        ScoreHistogramModel(),
        InvestigationSetModel(),
        RunArchiveListModel(),
    )

    assert controller.archiveCount == 1
    assert controller.open_run(run.run_id)
    assert controller.hasRun
    assert controller.sourceState == "available"
    assert controller.recordCount == 4

    controller.selectInvestigationSet("component_conflict")
    controller.inspectSelection()
    assert controller.activeTab == "records"
    assert predictions.rowCount() == 2
    assert predictions.data(predictions.index(0, 0)) == 2
    assert predictions.data(predictions.index(1, 0)) == 3

    controller.searchRecords("Pathogenic")
    assert controller.visibleRecordCount == 1

    controller.searchRecords("")
    controller.showOverview()
    controller.selectInvestigationSet("pathogenic")
    controller.showRecords()
    assert controller.selectionKey == "all"
    assert predictions.rowCount() == 4
