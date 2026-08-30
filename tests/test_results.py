from __future__ import annotations

from pathlib import Path
from concurrent.futures import Future

import pytest

from variant_inference.application.results import ResultSetSession
from variant_inference.domain.models import (
    LoadedVerifiedRun,
    PredictionRecord,
    RunArchiveEntry,
    SourceFieldEvidence,
    SourceReferenceState,
    SourceReferenceStatus,
    SourceRowEvidence,
)
from variant_inference.qt.results_controller import ResultsController
from variant_inference.qt.results_models import (
    InvestigationSetModel,
    PredictionTableModel,
    RunArchiveListModel,
    ScoreHistogramModel,
    SourceFieldListModel,
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


def test_prediction_table_exposes_accessible_source_and_column_roles():
    model = PredictionTableModel()
    model.set_records(loaded_run().predictions)

    index = model.index(2, 4)
    assert model.data(index, model.SourceRowRole) == 3
    assert model.data(index, model.ColumnLabelRole) == "LightGBM"


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


class FixedSourceEvidence:
    def read(self, run: LoadedVerifiedRun, source_row: int) -> SourceRowEvidence:
        return SourceRowEvidence(
            source_row=source_row,
            state=SourceReferenceState.AVAILABLE,
            expected_sha256=run.source_sha256,
            current_sha256=run.source_sha256,
            detail="Checksum-valid original Source Row recovered through read-only source access.",
            fields=(
                SourceFieldEvidence("Variant_ID", f"VAR-{source_row:03d}", "text"),
                SourceFieldEvidence("AL_1", str(source_row / 10), "number"),
            ),
        )

    def close(self) -> None:
        pass


class ImmediateExecutor:
    def submit(self, function, *args):
        future = Future()
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)
        return future


def test_results_controller_reopens_run_and_exposes_exact_selected_records():
    run = loaded_run()
    predictions = PredictionTableModel()
    source_fields = SourceFieldListModel()
    controller = ResultsController(
        MemoryArchive(run),
        predictions,
        ScoreHistogramModel(),
        InvestigationSetModel(),
        RunArchiveListModel(),
        FixedSourceEvidence(),
        source_fields,
        ImmediateExecutor(),
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

    controller.selectRecordAt(1)
    assert controller.hasSelectedRecord
    assert controller.selectedVisibleRow == 1
    assert controller.selectedSourceRow == 3
    assert controller.selectedPrediction == "Pathogenic"
    assert controller.selectedEnsembleScore == 0.62
    assert controller.selectedCatBoostScore == 0.58
    assert controller.selectedLightgbmScore == 0.66
    assert controller.selectedDisagreement == pytest.approx(0.04)
    assert controller.thresholdRelationship == "0.010000 above threshold"
    assert controller.sourceEvidenceState == "available"
    assert source_fields.rowCount() == 2
    assert source_fields.data(source_fields.index(0, 0), source_fields.NameRole) == "Variant_ID"
    assert source_fields.data(source_fields.index(0, 0), source_fields.ValueRole) == "VAR-003"

    controller.searchSourceFields("al_1")
    assert controller.visibleSourceFieldCount == 1
    assert source_fields.data(source_fields.index(0, 0), source_fields.NameRole) == "AL_1"

    controller.searchRecords("Pathogenic")
    assert controller.visibleRecordCount == 1

    controller.searchRecords("")
    controller.showOverview()
    controller.selectInvestigationSet("pathogenic")
    controller.showRecords()
    assert controller.selectionKey == "all"
    assert predictions.rowCount() == 4
