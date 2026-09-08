"""The official submission file must match the organisers' guide exactly.

The uploaded JSON is scored automatically and is the only artefact that counts.
A file the upload system rejects is not a late submission, it is no submission,
and after the window closes no other channel is accepted. These tests pin every
rule stated in section 3 of the final application guide.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from variant_inference.application.competition_export import (
    CompetitionExportError,
    CompetitionExportService,
    CompetitionTeam,
)
from variant_inference.domain.models import LoadedVerifiedRun, PredictionRecord
from variant_inference.infrastructure.csv_source import CsvSourceReader

TEAM = CompetitionTeam(
    team_name="Computational-Health-Lab",
    team_id="763095",
    application_id="4484264",
)

SOURCE = """Variant_ID,_panel,AL_1
Varyant_1,CFTR,0.10
Varyant_2,PAH,0.20
Varyant_3,KANSER,0.30
Varyant_4,MASTER,0.40
"""

SCORES = (0.9123456789, 0.2000000001, 0.7500000000, 0.1000000000)


def write_source(tmp_path: Path, text: str = SOURCE) -> Path:
    path = tmp_path / "final_test.csv"
    path.write_text(text, encoding="utf-8")
    return path


def run_for(path: Path, scores=SCORES, columns: int = 3) -> LoadedVerifiedRun:
    predictions = tuple(
        PredictionRecord(
            source_row=index + 1,
            ensemble_score=score,
            prediction="Pathogenic" if score >= 0.61 else "Benign",
            component_scores={"catboost": score, "lightgbm": score},
            model_disagreement=0.0,
        )
        for index, score in enumerate(scores)
    )
    return LoadedVerifiedRun(
        run_id="run-final",
        created_at="2026-09-16T13:00:00Z",
        completed_at="2026-09-16T13:00:09Z",
        duration_ms=9000,
        source_path=path,
        source_file_name=path.name,
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_row_count=len(scores),
        source_column_count=columns,
        model_package_name="TEKNOFEST 2026 PDR Release",
        model_package_version="1.0.0-pdr",
        model_package_manifest_checksum="c" * 64,
        inference_contract_id="contract",
        inference_contract_version="1",
        inference_contract_checksum="d" * 64,
        release_threshold=0.61,
        predictions_sha256="e" * 64,
        predictions=predictions,
    )


def export(tmp_path: Path, run: LoadedVerifiedRun, **kwargs):
    service = CompetitionExportService(CsvSourceReader())
    options = {
        "team": TEAM,
        "identifier_column": "Variant_ID",
        "panel_column": "_panel",
        **kwargs,
    }
    return service.export(run, tmp_path / "out" / "submission.json", **options)


def payload_of(report) -> dict:
    return json.loads(report.path.read_text(encoding="utf-8"))


# Header -------------------------------------------------------------------


def test_the_header_matches_the_registered_team_identity(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))

    assert payload["team_name"] == "Computational-Health-Lab"
    assert payload["team_id"] == "763095"
    assert payload["application_id"] == "4484264"
    assert payload["competition_level"] == "UNIVERSITE_VE_UZERI"


def test_an_incomplete_header_is_refused(tmp_path: Path) -> None:
    incomplete = CompetitionTeam(team_name="Computational-Health-Lab", team_id="", application_id="4484264")

    with pytest.raises(CompetitionExportError, match="team id"):
        export(tmp_path, run_for(write_source(tmp_path)), team=incomplete)


def test_the_suggested_file_name_follows_the_guide() -> None:
    service = CompetitionExportService(CsvSourceReader())
    assert service.suggested_file_name(TEAM) == "TEAM_763095_FINAL.json"


# Prediction records --------------------------------------------------------


def test_each_record_carries_exactly_the_four_required_fields(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))

    assert len(payload["predictions"]) == 4
    for item in payload["predictions"]:
        assert set(item) == {"id", "panel", "predicted_class", "predicted_prob"}


def test_identifiers_come_from_the_source_unaltered(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))

    assert [item["id"] for item in payload["predictions"]] == [
        "Varyant_1", "Varyant_2", "Varyant_3", "Varyant_4"
    ]


def test_the_panel_travels_with_each_record(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))

    assert [item["panel"] for item in payload["predictions"]] == [
        "CFTR", "PAH", "KANSER", "MASTER"
    ]


def test_the_class_is_the_string_zero_or_one(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))
    classes = [item["predicted_class"] for item in payload["predictions"]]

    assert classes == ["1", "0", "1", "0"]
    assert all(isinstance(value, str) for value in classes)


def test_the_probability_is_a_number_between_zero_and_one(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))

    for item, expected in zip(payload["predictions"], SCORES):
        assert isinstance(item["predicted_prob"], float)
        assert 0.0 <= item["predicted_prob"] <= 1.0
        assert item["predicted_prob"] == pytest.approx(expected)


def test_the_class_reflects_our_own_threshold_not_a_fixed_half(tmp_path: Path) -> None:
    """The guide states predicted_class must carry the team's final decision."""
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))
    by_id = {item["id"]: item for item in payload["predictions"]}

    # 0.75 is above our 0.61 threshold and would also be above 0.5.
    assert by_id["Varyant_3"]["predicted_class"] == "1"
    # 0.20 is below both, so this only confirms the mapping direction.
    assert by_id["Varyant_2"]["predicted_class"] == "0"


# Rules the organisers reject on -------------------------------------------


def test_a_duplicate_identifier_is_refused(tmp_path: Path) -> None:
    source = write_source(tmp_path, SOURCE.replace("Varyant_3", "Varyant_1"))

    with pytest.raises(CompetitionExportError, match="more than once"):
        export(tmp_path, run_for(source))


def test_an_empty_identifier_is_refused_rather_than_invented(tmp_path: Path) -> None:
    source = write_source(tmp_path, SOURCE.replace("Varyant_2", ""))

    with pytest.raises(CompetitionExportError, match="empty"):
        export(tmp_path, run_for(source))


def test_a_non_finite_probability_is_refused(tmp_path: Path) -> None:
    source = write_source(tmp_path)
    run = run_for(source, scores=(float("nan"), 0.2, 0.75, 0.1))

    with pytest.raises(CompetitionExportError, match="finite"):
        export(tmp_path, run)


def test_the_written_file_is_parseable_utf8_json(tmp_path: Path) -> None:
    report = export(tmp_path, run_for(write_source(tmp_path)))
    raw = report.path.read_bytes()

    assert report.path.suffix == ".json"
    json.loads(raw.decode("utf-8"))
    assert b"NaN" not in raw and b"Infinity" not in raw


def test_a_refused_export_leaves_no_partial_file(tmp_path: Path) -> None:
    source = write_source(tmp_path, SOURCE.replace("Varyant_3", "Varyant_1"))

    with pytest.raises(CompetitionExportError):
        export(tmp_path, run_for(source))

    assert not (tmp_path / "out" / "submission.json").exists()


# Source boundary -----------------------------------------------------------


def test_a_modified_source_is_refused(tmp_path: Path) -> None:
    source = write_source(tmp_path)
    run = run_for(source)
    source.write_text(SOURCE.replace("CFTR", "EDITED"), encoding="utf-8")

    with pytest.raises(CompetitionExportError, match="changed"):
        export(tmp_path, run)


def test_a_missing_source_is_refused(tmp_path: Path) -> None:
    source = write_source(tmp_path)
    run = run_for(source)
    source.unlink()

    with pytest.raises(CompetitionExportError, match="missing"):
        export(tmp_path, run)


def test_an_absent_identifier_column_is_refused(tmp_path: Path) -> None:
    with pytest.raises(CompetitionExportError, match="identifier column"):
        export(tmp_path, run_for(write_source(tmp_path)), identifier_column="NoSuchColumn")


# Order and completeness ----------------------------------------------------


def test_every_prediction_appears_exactly_once(tmp_path: Path) -> None:
    report = export(tmp_path, run_for(write_source(tmp_path)))
    payload = payload_of(report)
    identifiers = [item["id"] for item in payload["predictions"]]

    assert report.record_count == 4
    assert len(identifiers) == len(set(identifiers)) == 4


def test_records_are_written_in_source_row_order(tmp_path: Path) -> None:
    payload = payload_of(export(tmp_path, run_for(write_source(tmp_path))))

    assert [item["id"] for item in payload["predictions"]] == sorted(
        item["id"] for item in payload["predictions"]
    )


def test_the_report_summarises_what_was_written(tmp_path: Path) -> None:
    report = export(tmp_path, run_for(write_source(tmp_path)))

    assert report.record_count == 4
    assert report.pathogenic_count == 2
    assert report.benign_count == 2
    assert report.identifier_column == "Variant_ID"
    assert report.profile_id == "teknofest-2026-final-v1"
    assert any("unique identifiers" in check for check in report.checks)


def test_a_blank_panel_is_reported_but_not_fatal(tmp_path: Path) -> None:
    """The guide fixes the class names but does not constrain panel values."""
    report = export(tmp_path, run_for(write_source(tmp_path, SOURCE.replace(",PAH,", ",,"))))

    assert report.record_count == 4
    assert any("empty panel" in check for check in report.checks)


# Controller ----------------------------------------------------------------


class _Results:
    """Minimal stand-in for the results controller the surface follows."""

    def __init__(self, run=None) -> None:
        self.current_run = run


class _Immediate:
    def submit(self, function, *arguments):
        from concurrent.futures import Future

        future: Future = Future()
        try:
            future.set_result(function(*arguments))
        except BaseException as error:  # noqa: BLE001
            future.set_exception(error)
        return future


def controller_for(run):
    from variant_inference.qt.submission_controller import SubmissionController

    results = _Results(run)
    controller = SubmissionController(
        CompetitionExportService(CsvSourceReader()), results, TEAM, _Immediate()
    )
    controller._follow_run()  # the surface follows the results controller's signal
    return controller


def test_the_controller_proposes_familiar_columns(tmp_path: Path) -> None:
    controller = controller_for(run_for(write_source(tmp_path)))

    assert controller.identifierColumn == "Variant_ID"
    assert controller.panelColumn == "_panel"
    assert controller.canWrite is True


def test_an_unfamiliar_identifier_column_is_not_guessed(tmp_path: Path) -> None:
    """Identifiers are never invented, so the operator must name the column."""
    text = SOURCE.replace("Variant_ID", "kayit_no")
    controller = controller_for(run_for(write_source(tmp_path, text)))

    assert controller.identifierColumn == ""
    assert controller.canWrite is False
    assert controller.messageKind == "warning"

    controller.selectIdentifierColumn("kayit_no")

    assert controller.canWrite is True


def test_the_controller_writes_and_reports_the_checks(tmp_path: Path) -> None:
    controller = controller_for(run_for(write_source(tmp_path)))

    controller.writeSubmission(str(tmp_path / "TEAM_763095_FINAL.json"))

    assert controller.messageKind == "success"
    assert "300" not in controller.message
    assert Path(controller.writtenPath).is_file()
    assert any("unique identifiers" in check for check in controller.checks)


def test_a_refused_submission_reports_the_broken_rule(tmp_path: Path) -> None:
    source = write_source(tmp_path, SOURCE.replace("Varyant_3", "Varyant_1"))
    controller = controller_for(run_for(source))

    controller.writeSubmission(str(tmp_path / "out.json"))

    assert controller.messageKind == "error"
    assert "more than once" in controller.message
    assert controller.writtenPath == ""
    assert controller.checks == []
    assert controller.busy is False


def test_the_header_is_exposed_for_display(tmp_path: Path) -> None:
    controller = controller_for(run_for(write_source(tmp_path)))

    assert controller.teamName == "Computational-Health-Lab"
    assert controller.teamId == "763095"
    assert controller.applicationId == "4484264"
    assert controller.competitionLevel == "UNIVERSITE_VE_UZERI"
    assert controller.suggestedFileName == "TEAM_763095_FINAL.json"


def test_without_a_run_nothing_can_be_written(tmp_path: Path) -> None:
    controller = controller_for(None)

    assert controller.hasRun is False
    assert controller.canWrite is False

    controller.writeSubmission(str(tmp_path / "out.json"))

    assert not (tmp_path / "out.json").exists()


def test_choosing_a_label_column_as_identifier_is_reported_immediately(tmp_path: Path) -> None:
    """A label column has few distinct values, so it cannot identify records.

    Reported on selection rather than at write time: during a timed final,
    finding out after clicking wastes a cycle.
    """
    text = "Variant_ID,_panel,label\nA,CFTR,1\nB,PAH,0\nC,KANSER,1\nD,MASTER,0\n"
    controller = controller_for(run_for(write_source(tmp_path, text)))

    controller.selectIdentifierColumn("label")

    assert controller.messageKind == "error"
    assert "cannot be the record identifier" in controller.message


def test_a_valid_identifier_column_reports_readiness(tmp_path: Path) -> None:
    controller = controller_for(run_for(write_source(tmp_path)))

    controller.selectIdentifierColumn("Variant_ID")

    assert controller.messageKind == "neutral"
    assert "Variant_ID" in controller.message
    assert controller.canWrite is True


def test_the_message_follows_the_current_choice(tmp_path: Path) -> None:
    """Regression: the message was set once on load and left stale afterwards."""
    text = SOURCE.replace("Variant_ID", "kayit_no")
    controller = controller_for(run_for(write_source(tmp_path, text)))
    assert controller.messageKind == "warning"

    controller.selectIdentifierColumn("kayit_no")

    assert controller.messageKind != "warning"
    assert "No familiar identifier column" not in controller.message


def test_a_rejected_identifier_column_disables_writing(tmp_path: Path) -> None:
    """An enabled button beside a red refusal message is a contradiction."""
    text = "Variant_ID,_panel,label\nA,CFTR,1\nB,PAH,0\nC,KANSER,1\nD,MASTER,0\n"
    controller = controller_for(run_for(write_source(tmp_path, text)))

    controller.selectIdentifierColumn("label")
    assert controller.canWrite is False

    controller.selectIdentifierColumn("Variant_ID")
    assert controller.canWrite is True
