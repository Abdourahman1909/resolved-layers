from __future__ import annotations

import hashlib
from concurrent.futures import Future
from pathlib import Path

import pytest

from variant_inference.application.evaluation import (
    EvaluationUnavailableError,
    GroundTruthEvaluationService,
)
from variant_inference.domain.models import (
    GroundTruthAuthorization,
    LoadedVerifiedRun,
    PredictionRecord,
    SourceReferenceState,
    SourceReferenceStatus,
)
from variant_inference.infrastructure.csv_source import CsvSourceReader
from variant_inference.qt.evaluation_controller import EvaluationController
from variant_inference.qt.evaluation_models import EvaluationCohortModel, EvaluationMetricModel


def evaluation_run(source_path: Path, labels: tuple[str, ...]) -> LoadedVerifiedRun:
    predictions = (
        PredictionRecord(1, 0.90, "Pathogenic", {"catboost": 0.92, "lightgbm": 0.88}, 0.02),
        PredictionRecord(2, 0.20, "Benign", {"catboost": 0.18, "lightgbm": 0.22}, 0.02),
        PredictionRecord(3, 0.80, "Pathogenic", {"catboost": 0.82, "lightgbm": 0.78}, 0.02),
        PredictionRecord(4, 0.10, "Benign", {"catboost": 0.08, "lightgbm": 0.12}, 0.02),
        PredictionRecord(5, 0.70, "Pathogenic", {"catboost": 0.72, "lightgbm": 0.68}, 0.02),
        PredictionRecord(6, 0.30, "Benign", {"catboost": 0.28, "lightgbm": 0.32}, 0.02),
    )
    assert len(labels) == len(predictions)
    checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return LoadedVerifiedRun(
        run_id="run-evaluation",
        created_at="2026-08-30T12:00:00+00:00",
        completed_at="2026-08-30T12:00:01+00:00",
        duration_ms=1000,
        source_path=source_path,
        source_file_name=source_path.name,
        source_sha256=checksum,
        source_row_count=len(predictions),
        source_column_count=3,
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


class MemoryArchive:
    def __init__(self, status: SourceReferenceStatus) -> None:
        self.status = status

    def source_status(self, run_id: str) -> SourceReferenceStatus:
        assert run_id == "run-evaluation"
        return self.status


class ImmediateExecutor:
    def submit(self, function, *args):
        future = Future()
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)
        return future


class DeferredExecutor:
    def __init__(self) -> None:
        self.tasks = []

    def submit(self, function, *args):
        future = Future()
        self.tasks.append((function, args, future))
        return future

    def run_next(self) -> None:
        function, args, future = self.tasks.pop(0)
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)


def write_source(path: Path, labels: tuple[str, ...]) -> None:
    rows = ["Variant_ID,GroundTruth,_panel"]
    rows.extend(
        f"VAR-{index:03d},{label},PANEL-{1 if index <= 3 else 2}"
        for index, label in enumerate(labels, 1)
    )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def service_for(run: LoadedVerifiedRun) -> GroundTruthEvaluationService:
    status = SourceReferenceStatus(
        SourceReferenceState.AVAILABLE,
        run.source_sha256,
        run.source_sha256,
    )
    return GroundTruthEvaluationService(MemoryArchive(status), CsvSourceReader())


def test_evaluation_requires_explicit_mapping_and_joins_by_exact_source_row(tmp_path):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "labeled.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)
    service = service_for(run)

    evidence = service.prepare(run)
    assert evidence.state is SourceReferenceState.AVAILABLE
    assert evidence.label_columns == ("Variant_ID", "GroundTruth", "_panel")
    assert evidence.selected_column == ""
    assert service.label_values(run, "GroundTruth") == ("case", "control", "pending")

    report = service.evaluate(
        run,
        GroundTruthAuthorization("GroundTruth", "case", "control"),
    )

    assert report.total_records == 6
    assert report.evaluated_count == 4
    assert report.missing_count == 1
    assert report.unrecognized_count == 1
    assert report.excluded_count == 2
    assert (report.true_positive, report.false_positive, report.false_negative, report.true_negative) == (
        1,
        1,
        1,
        1,
    )
    assert report.metric("f1").value == pytest.approx(0.5)
    assert report.metric("precision").value == pytest.approx(0.5)
    assert report.metric("recall").value == pytest.approx(0.5)
    assert report.metric("mcc").value == pytest.approx(0.0)
    assert report.metric("accuracy").value == pytest.approx(0.5)
    assert report.cohort("false_positive").source_rows == (3,)
    assert report.cohort("false_negative").source_rows == (2,)
    assert report.cohort("true_positive").source_rows == (1,)
    assert report.cohort("true_negative").source_rows == (4,)

    preview = service.preview(run, GroundTruthAuthorization("GroundTruth", "case", "control"))
    assert preview.total == 6
    assert preview.recognized == 4
    assert preview.missing == 1
    assert preview.unrecognized == 1


def test_evaluation_rejects_a_source_that_changes_while_it_is_opened(tmp_path):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "changes-while-opening.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)

    class MutatingReader:
        def open(self, path):
            source = CsvSourceReader().open(path)
            path.write_text(
                path.read_text(encoding="utf-8").replace("VAR-001,case", "VAR-001,late"),
                encoding="utf-8",
            )
            return source

    service = GroundTruthEvaluationService(
        MemoryArchive(
            SourceReferenceStatus(
                SourceReferenceState.AVAILABLE,
                run.source_sha256,
                run.source_sha256,
            )
        ),
        MutatingReader(),
    )

    with pytest.raises(EvaluationUnavailableError, match="changed while Evaluation was opening"):
        service.evaluate(
            run,
            GroundTruthAuthorization("GroundTruth", "case", "control"),
        )


def test_evaluation_treats_raw_mappings_as_exact_and_discloses_ambiguous_rows(tmp_path):
    labels = ("case", "Case", "control", "control", "", "pending")
    source_path = tmp_path / "case-sensitive.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)

    report = service_for(run).evaluate(
        run,
        GroundTruthAuthorization("GroundTruth", "case", "control"),
    )

    assert report.evaluated_count == 3
    assert report.missing_count == 1
    assert report.unrecognized_count == 2
    assert report.unrecognized_source_rows == (2, 6)
    assert report.missing_source_rows == (5,)


def test_zero_denominators_are_reported_as_undefined_not_fabricated(tmp_path):
    labels = ("control", "control")
    source_path = tmp_path / "all-benign.csv"
    source_path.write_text(
        "Variant_ID,GroundTruth,_panel\nVAR-001,control,PANEL-1\nVAR-002,control,PANEL-1\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    predictions = (
        PredictionRecord(1, 0.10, "Benign", {"catboost": 0.08, "lightgbm": 0.12}, 0.02),
        PredictionRecord(2, 0.20, "Benign", {"catboost": 0.18, "lightgbm": 0.22}, 0.02),
    )
    run = LoadedVerifiedRun(
        run_id="run-evaluation",
        created_at="2026-08-30T12:00:00+00:00",
        completed_at="2026-08-30T12:00:01+00:00",
        duration_ms=1000,
        source_path=source_path,
        source_file_name=source_path.name,
        source_sha256=checksum,
        source_row_count=2,
        source_column_count=3,
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

    report = service_for(run).evaluate(
        run,
        GroundTruthAuthorization("GroundTruth", "case", "control"),
    )

    for key in ("f1", "precision", "recall", "mcc"):
        assert report.metric(key).value is None
        assert report.metric(key).display == "Undefined"
        assert report.metric(key).denominator == 0
    assert report.metric("accuracy").value == pytest.approx(1.0)


@pytest.mark.parametrize("state", [SourceReferenceState.MISSING, SourceReferenceState.MODIFIED])
def test_evaluation_never_reads_or_calculates_when_source_is_not_checksum_valid(tmp_path, state):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "unavailable.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)
    current = "9" * 64 if state is SourceReferenceState.MODIFIED else ""
    service = GroundTruthEvaluationService(
        MemoryArchive(SourceReferenceStatus(state, run.source_sha256, current)),
        CsvSourceReader(),
    )

    evidence = service.prepare(run)
    assert evidence.state is state
    assert evidence.label_columns == ()
    with pytest.raises(EvaluationUnavailableError, match="checksum-valid"):
        service.evaluate(
            run,
            GroundTruthAuthorization("GroundTruth", "case", "control"),
        )


def test_evaluation_controller_never_selects_or_authorizes_ground_truth_implicitly(tmp_path):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "controller.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)
    metrics = EvaluationMetricModel()
    cohorts = EvaluationCohortModel()
    controller = EvaluationController(service_for(run), metrics, cohorts, ImmediateExecutor())

    controller.load_run(run)

    assert controller.hasRun
    assert controller.sourceState == "available"
    assert controller.selectedLabelColumn == ""
    assert not controller.evaluationAuthorized
    assert not controller.hasReport
    assert controller.labelValues == []

    controller.selectLabelColumn("GroundTruth")
    assert controller.labelValues == ["case", "control", "pending"]
    assert not controller.evaluationAuthorized

    controller.authorizeEvaluation("case", "control")
    assert not controller.evaluationAuthorized
    assert "Review valid, missing" in controller.errorMessage

    controller.reviewCoverage("case", "control")
    assert controller.hasCoveragePreview
    assert controller.previewEvaluatedCount == 4
    assert controller.previewMissingCount == 1
    assert controller.previewUnrecognizedCount == 1

    controller.authorizeEvaluation("case", "control")
    assert controller.evaluationAuthorized
    assert controller.hasReport
    assert controller.evaluatedCount == 4
    assert controller.excludedCount == 2
    assert metrics.rowCount() == 5
    assert cohorts.rowCount() == 4
    assert controller.cohort_source_rows("false_positive") == (3,)

    controller.selectLabelColumn("_panel")
    assert not controller.evaluationAuthorized
    assert not controller.hasReport
    assert metrics.rowCount() == 0
    assert cohorts.rowCount() == 0


def test_evaluation_controller_schedules_source_work_without_blocking_the_ui_slot(tmp_path):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "async-controller.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)
    executor = DeferredExecutor()
    controller = EvaluationController(
        service_for(run),
        EvaluationMetricModel(),
        EvaluationCohortModel(),
        executor,
    )

    controller.load_run(run)

    assert controller.busy
    assert len(executor.tasks) == 1
    assert not controller.sourceAvailable

    executor.run_next()

    assert not controller.busy
    assert controller.sourceAvailable


def test_evaluation_controller_withholds_metrics_if_source_changes_before_authorization(tmp_path):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "changes-before-authorization.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)
    archive = MemoryArchive(
        SourceReferenceStatus(
            SourceReferenceState.AVAILABLE,
            run.source_sha256,
            run.source_sha256,
        )
    )
    controller = EvaluationController(
        GroundTruthEvaluationService(archive, CsvSourceReader()),
        EvaluationMetricModel(),
        EvaluationCohortModel(),
        ImmediateExecutor(),
    )
    controller.load_run(run)
    controller.selectLabelColumn("GroundTruth")
    controller.reviewCoverage("case", "control")

    archive.status = SourceReferenceStatus(
        SourceReferenceState.MODIFIED,
        run.source_sha256,
        "9" * 64,
    )
    controller.authorizeEvaluation("case", "control")

    assert controller.sourceState == "modified"
    assert not controller.evaluationAuthorized
    assert not controller.hasReport
    assert "checksum-valid" in controller.errorMessage


def test_evaluation_controller_fails_closed_when_archive_source_status_errors(tmp_path):
    labels = ("case", "case", "control", "control", "", "pending")
    source_path = tmp_path / "archive-failure.csv"
    write_source(source_path, labels)
    run = evaluation_run(source_path, labels)

    class FailingArchive(MemoryArchive):
        fail = False

        def source_status(self, run_id: str) -> SourceReferenceStatus:
            if self.fail:
                raise RuntimeError("Run archive manifest is unreadable.")
            return super().source_status(run_id)

    archive = FailingArchive(
        SourceReferenceStatus(
            SourceReferenceState.AVAILABLE,
            run.source_sha256,
            run.source_sha256,
        )
    )
    controller = EvaluationController(
        GroundTruthEvaluationService(archive, CsvSourceReader()),
        EvaluationMetricModel(),
        EvaluationCohortModel(),
        ImmediateExecutor(),
    )
    controller.load_run(run)
    controller.selectLabelColumn("GroundTruth")
    controller.reviewCoverage("case", "control")
    controller.authorizeEvaluation("case", "control")
    assert controller.hasReport

    archive.fail = True
    controller.refreshSource()

    assert not controller.hasReport
    assert controller.sourceState == "missing"
    assert "manifest is unreadable" in controller.errorMessage
