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


# Group breakdown ----------------------------------------------------------
#
# The competition scores this workflow per panel, not over the pooled cohort,
# so a healthy pooled figure can hide a weak individual group.


def grouped_report(tmp_path, labels, group_by="_panel"):
    source = tmp_path / "grouped.csv"
    write_source(source, labels)
    run = evaluation_run(source, labels)
    authorization = GroundTruthAuthorization("GroundTruth", "case", "control")
    return service_for(run).evaluate(run, authorization, group_by=group_by)


# Predictions are Pathogenic on rows 1, 3, 5 and Benign on rows 2, 4, 6.
# PANEL-1 holds rows 1-3, PANEL-2 holds rows 4-6.
MIXED = ("case", "control", "control", "control", "case", "case")


def test_grouping_is_opt_in(tmp_path) -> None:
    assert grouped_report(tmp_path, MIXED, group_by=None).grouping is None


def test_each_group_is_scored_separately(tmp_path) -> None:
    grouping = grouped_report(tmp_path, MIXED).grouping

    assert grouping is not None
    assert [g.value for g in grouping.groups] == ["PANEL-1", "PANEL-2"]

    first, second = grouping.groups
    # PANEL-1: row1 TP, row2 TN, row3 FP
    assert (first.true_positive, first.false_positive, first.false_negative, first.true_negative) == (1, 1, 0, 1)
    # PANEL-2: row4 TN, row5 TP, row6 FN
    assert (second.true_positive, second.false_positive, second.false_negative, second.true_negative) == (1, 0, 1, 1)


def test_groups_reconcile_with_the_pooled_confusion_matrix(tmp_path) -> None:
    report = grouped_report(tmp_path, MIXED)
    groups = report.grouping.groups

    for attribute in ("true_positive", "false_positive", "false_negative", "true_negative"):
        assert sum(getattr(g, attribute) for g in groups) == getattr(report, attribute)
    assert sum(g.evaluated_count for g in groups) == report.evaluated_count


# PANEL-1 fully correct, PANEL-2 fully wrong. Pooled F1 sits between them.
ASYMMETRIC = ("case", "control", "case", "case", "control", "case")


def test_a_group_can_score_worse_than_the_pooled_cohort(tmp_path) -> None:
    """The reason this feature exists: pooling hides a weak group."""
    report = grouped_report(tmp_path, ASYMMETRIC)
    pooled = report.metric("f1").value
    per_group = [g.metric("f1").value for g in report.grouping.groups]

    assert pooled == pytest.approx(4 / 7)
    assert per_group == [pytest.approx(1.0), pytest.approx(0.0)]
    assert min(per_group) < pooled


def test_the_mean_weights_every_group_equally(tmp_path) -> None:
    grouping = grouped_report(tmp_path, MIXED).grouping
    values = [g.metric("f1").value for g in grouping.groups]

    assert grouping.mean("f1") == pytest.approx(sum(values) / len(values))


def test_an_undefined_group_metric_makes_the_mean_undefined(tmp_path) -> None:
    """A group with no positive predictions and no positive labels leaves F1
    undefined. Averaging the remaining groups would quietly overstate it."""
    # Excluding row 5 leaves PANEL-2 with only Benign predictions on Benign
    # labels, so it has no TP, FP or FN and F1 has no denominator.
    labels = ("case", "control", "control", "control", "", "control")
    grouping = grouped_report(tmp_path, labels).grouping

    assert any(g.metric("f1").value is None for g in grouping.groups)
    assert grouping.mean("f1") is None
    assert grouping.mean_display("f1") == "Undefined"


def test_rows_excluded_from_evaluation_stay_out_of_every_group(tmp_path) -> None:
    labels = ("case", "", "unknown-value", "control", "case", "case")
    report = grouped_report(tmp_path, labels)

    assert report.missing_count == 1
    assert report.unrecognized_count == 1
    assert sum(g.evaluated_count for g in report.grouping.groups) == report.evaluated_count
    every_row = {row for g in report.grouping.groups for row in g.source_rows}
    assert 2 not in every_row and 3 not in every_row


def test_grouping_reports_the_column_it_used(tmp_path) -> None:
    assert grouped_report(tmp_path, MIXED).grouping.column_name == "_panel"


def test_an_absent_grouping_column_is_refused(tmp_path) -> None:
    with pytest.raises(ValueError, match="absent"):
        grouped_report(tmp_path, MIXED, group_by="NoSuchColumn")


def test_blank_group_values_are_named_rather_than_dropped(tmp_path) -> None:
    source = tmp_path / "blank.csv"
    source.write_text(
        "Variant_ID,GroundTruth,_panel\n"
        "VAR-001,case,\nVAR-002,control,\nVAR-003,control,P\n"
        "VAR-004,control,P\nVAR-005,case,P\nVAR-006,case,P\n",
        encoding="utf-8",
    )
    run = evaluation_run(source, MIXED)
    report = service_for(run).evaluate(
        run, GroundTruthAuthorization("GroundTruth", "case", "control"), group_by="_panel"
    )

    values = [g.value for g in report.grouping.groups]
    assert "(missing)" in values
    assert sum(g.evaluated_count for g in report.grouping.groups) == report.evaluated_count


def grouping_controller(tmp_path):
    from variant_inference.qt.evaluation_models import EvaluationGroupModel

    source = tmp_path / "controller.csv"
    write_source(source, ASYMMETRIC)
    run = evaluation_run(source, ASYMMETRIC)
    groups = EvaluationGroupModel()
    controller = EvaluationController(
        service_for(run),
        EvaluationMetricModel(),
        EvaluationCohortModel(),
        ImmediateExecutor(),
        groups=groups,
    )
    controller.load_run(run)
    controller.selectLabelColumn("GroundTruth")
    # Coverage must be reviewed before authorization; the controller refuses
    # to authorize a mapping the operator has not seen the counts for.
    controller.reviewCoverage("case", "control")
    controller.authorizeEvaluation("case", "control")
    return controller, groups


def test_controller_does_not_group_until_asked(tmp_path) -> None:
    controller, groups = grouping_controller(tmp_path)

    assert controller.hasReport
    assert controller.hasGrouping is False
    assert groups.rowCount() == 0
    assert controller.meanGroupF1 == "—"


def test_controller_groups_on_request_and_reports_the_equal_weighted_mean(tmp_path) -> None:
    controller, groups = grouping_controller(tmp_path)

    controller.selectGroupColumn("_panel")

    assert controller.hasGrouping is True
    assert controller.groupCount == 2
    assert groups.rowCount() == 2
    # PANEL-1 scores 1.0 and PANEL-2 scores 0.0; the equal-weighted mean is 0.5,
    # while the pooled F1 is 4/7. The mean is not the pooled figure.
    assert controller.meanGroupF1 == "0.5000"
    pooled = controller._report.metric("f1").value
    assert pooled == pytest.approx(4 / 7)
    assert controller.meanGroupF1 != f"{pooled:.4f}"


def test_controller_can_stop_grouping(tmp_path) -> None:
    controller, groups = grouping_controller(tmp_path)
    controller.selectGroupColumn("_panel")

    controller.selectGroupColumn("")

    assert controller.hasGrouping is False
    assert groups.rowCount() == 0


def test_controller_refuses_a_column_the_source_does_not_have(tmp_path) -> None:
    controller, _ = grouping_controller(tmp_path)

    controller.selectGroupColumn("NoSuchColumn")

    assert controller.groupColumn == ""
    assert "not an available source column" in controller.errorMessage


def test_the_authorized_label_column_is_not_offered_for_grouping(tmp_path) -> None:
    """Grouping by the label column would only restate the confusion matrix."""
    controller, _ = grouping_controller(tmp_path)

    assert "GroundTruth" not in controller.groupColumns
    assert "_panel" in controller.groupColumns
