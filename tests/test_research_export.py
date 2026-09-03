"""Exporting a Verified Run as a file someone else can open.

The two properties that make an export defensible are pinned here: it is built
only from a checksum-valid Source Dataset, and its row order is Source Row
order regardless of how the operator was looking at the table.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from variant_inference.application.research_export import (
    ResearchExportError,
    ResearchExportService,
)
from variant_inference.domain.models import LoadedVerifiedRun, PredictionRecord
from variant_inference.infrastructure.csv_source import CsvSourceReader

SOURCE_TEXT = """Variant_ID,gene,note
VAR-1,BRCA1,first
VAR-2,CFTR,second
VAR-3,PAH,third
VAR-4,BRCA1,fourth
"""


def write_source(tmp_path: Path, text: str = SOURCE_TEXT) -> Path:
    path = tmp_path / "source.csv"
    path.write_text(text, encoding="utf-8")
    return path


def run_for(source_path: Path, *, columns: int = 3, rows: int = 4) -> LoadedVerifiedRun:
    scores = ((0.90, 0.88, 0.92), (0.20, 0.18, 0.22), (0.64, 0.71, 0.57), (0.10, 0.09, 0.11))
    predictions = tuple(
        PredictionRecord(
            source_row=index + 1,
            ensemble_score=ensemble,
            prediction="Pathogenic" if ensemble >= 0.61 else "Benign",
            component_scores={"catboost": catboost, "lightgbm": lightgbm},
            model_disagreement=abs(catboost - lightgbm),
        )
        for index, (ensemble, catboost, lightgbm) in enumerate(scores[:rows])
    )
    return LoadedVerifiedRun(
        run_id="run-test",
        created_at="2026-09-03T10:00:00Z",
        completed_at="2026-09-03T10:00:05Z",
        duration_ms=5000,
        source_path=source_path,
        source_file_name=source_path.name,
        source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        source_row_count=rows,
        source_column_count=columns,
        model_package_name="Test Package",
        model_package_version="1.0.0",
        model_package_manifest_checksum="c" * 64,
        inference_contract_id="contract-test",
        inference_contract_version="1",
        inference_contract_checksum="d" * 64,
        release_threshold=0.61,
        predictions_sha256="e" * 64,
        predictions=predictions,
    )


def export(tmp_path: Path, source_path: Path, run: LoadedVerifiedRun):
    service = ResearchExportService(CsvSourceReader())
    return service.export(run, tmp_path / "out" / "export.csv")


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    return rows[0], rows[1:]


# Content ------------------------------------------------------------------


def test_every_original_column_is_preserved(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    header, rows = read_csv(report.csv_path)

    assert header[:3] == ["Variant_ID", "gene", "note"]
    assert [row[:3] for row in rows] == [
        ["VAR-1", "BRCA1", "first"],
        ["VAR-2", "CFTR", "second"],
        ["VAR-3", "PAH", "third"],
        ["VAR-4", "BRCA1", "fourth"],
    ]


def test_predictions_and_component_scores_are_appended(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    header, rows = read_csv(report.csv_path)
    index = {name: position for position, name in enumerate(header)}

    assert set(report.added_columns) == {
        "source_row",
        "prediction",
        "ensemble_score",
        "model_disagreement",
        "catboost_score",
        "lightgbm_score",
    }
    assert rows[0][index["prediction"]] == "Pathogenic"
    assert rows[1][index["prediction"]] == "Benign"
    assert float(rows[0][index["ensemble_score"]]) == pytest.approx(0.90)
    assert float(rows[2][index["catboost_score"]]) == pytest.approx(0.71)


def test_row_count_matches_the_run(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    _, rows = read_csv(report.csv_path)

    assert report.row_count == 4
    assert len(rows) == 4


# Order --------------------------------------------------------------------


def test_a_run_cannot_even_hold_reordered_predictions(tmp_path: Path) -> None:
    """Order is guaranteed upstream, so no export path can emit a sorted file."""
    source_path = write_source(tmp_path)
    run = run_for(source_path)
    fields = {**run.__dict__, "predictions": tuple(reversed(run.predictions))}

    with pytest.raises(ValueError, match="preserve every Source Row in order"):
        LoadedVerifiedRun(**fields)


def test_exported_rows_ascend_by_source_row(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    header, rows = read_csv(report.csv_path)
    index = header.index("source_row")

    assert [row[index] for row in rows] == ["1", "2", "3", "4"]


def test_each_row_carries_its_own_source_values(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    header, rows = read_csv(report.csv_path)
    variant = header.index("Variant_ID")
    source_row = header.index("source_row")

    for row in rows:
        assert row[variant] == f"VAR-{row[source_row]}"


# Source boundary ----------------------------------------------------------


def test_a_modified_source_is_refused(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    run = run_for(source_path)
    source_path.write_text(SOURCE_TEXT.replace("BRCA1", "EDITED"), encoding="utf-8")

    with pytest.raises(ResearchExportError, match="changed"):
        export(tmp_path, source_path, run)


def test_a_missing_source_is_refused(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    run = run_for(source_path)
    source_path.unlink()

    with pytest.raises(ResearchExportError, match="missing"):
        export(tmp_path, source_path, run)


def test_a_refused_export_leaves_no_partial_file(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    run = run_for(source_path)
    source_path.write_text("Variant_ID,gene,note\nVAR-9,X,y\n", encoding="utf-8")

    with pytest.raises(ResearchExportError):
        export(tmp_path, source_path, run)

    assert not (tmp_path / "out" / "export.csv").exists()


# Column naming ------------------------------------------------------------


def test_a_source_column_named_prediction_is_not_shadowed(tmp_path: Path) -> None:
    text = "Variant_ID,prediction\nVAR-1,original-1\nVAR-2,original-2\n"
    source_path = write_source(tmp_path, text)
    report = export(tmp_path, source_path, run_for(source_path, columns=2, rows=2))

    header, rows = read_csv(report.csv_path)

    assert header.count("prediction") == 1
    assert "prediction__resolved_layers" in header
    assert rows[0][header.index("prediction")] == "original-1"
    assert rows[0][header.index("prediction__resolved_layers")] == "Pathogenic"


# Evidence sidecar ---------------------------------------------------------


def test_a_sidecar_records_what_produced_the_file(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    evidence = json.loads(report.evidence_path.read_text(encoding="utf-8"))

    assert evidence["run_id"] == "run-test"
    assert evidence["row_order"] == "source_row"
    assert evidence["source"]["sha256"] == run_for(source_path).source_sha256
    assert evidence["model_package"]["name"] == "Test Package"
    assert evidence["release_threshold"] == 0.61


def test_the_sidecar_does_not_claim_to_be_a_competition_submission(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    report = export(tmp_path, source_path, run_for(source_path))

    evidence = json.loads(report.evidence_path.read_text(encoding="utf-8"))

    assert evidence["export_kind"] == "research"
    assert "not an official" in evidence["note"].lower()


def test_a_csv_suffix_is_enforced(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    service = ResearchExportService(CsvSourceReader())

    report = service.export(run_for(source_path), tmp_path / "chosen-name")

    assert report.csv_path.suffix == ".csv"
    assert report.evidence_path.name.endswith(".evidence.json")


# Controller ---------------------------------------------------------------


class _StubResults:
    def __init__(self, run: LoadedVerifiedRun | None) -> None:
        self.current_run = run


def _controller(run, tmp_path):
    from concurrent.futures import Future

    from variant_inference.qt.export_controller import ExportController

    class Immediate:
        """Run the export inline so the test observes a settled state."""

        def submit(self, function, *arguments):
            future: Future = Future()
            try:
                future.set_result(function(*arguments))
            except BaseException as error:  # noqa: BLE001
                future.set_exception(error)
            return future

    return ExportController(
        ResearchExportService(CsvSourceReader()), _StubResults(run), executor=Immediate()
    )


def test_the_controller_refuses_to_export_without_a_run(tmp_path: Path) -> None:
    controller = _controller(None, tmp_path)

    controller.exportResearchCsv(str(tmp_path / "out.csv"))

    assert controller.canExport is False
    assert controller.messageKind == "error"
    assert "Verified Run" in controller.message


def test_the_controller_reports_a_written_export(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    controller = _controller(run_for(source_path), tmp_path)

    controller.exportResearchCsv(str(tmp_path / "out.csv"))

    assert controller.messageKind == "success"
    assert "736" not in controller.message
    assert controller.lastExportPath.endswith("out.csv")
    assert Path(controller.lastExportPath).is_file()


def test_the_controller_reports_a_modified_source_and_keeps_no_stale_path(
    tmp_path: Path,
) -> None:
    source_path = write_source(tmp_path)
    run = run_for(source_path)
    source_path.write_text(SOURCE_TEXT.replace("PAH", "EDITED"), encoding="utf-8")
    controller = _controller(run, tmp_path)

    controller.exportResearchCsv(str(tmp_path / "out.csv"))

    assert controller.messageKind == "error"
    assert controller.lastExportPath == ""
    assert controller.busy is False


def test_the_suggested_file_name_follows_the_source(tmp_path: Path) -> None:
    source_path = write_source(tmp_path)
    controller = _controller(run_for(source_path), tmp_path)

    assert controller.suggestedFileName == "source-predictions.csv"


def test_the_export_action_becomes_available_when_a_run_opens(tmp_path: Path) -> None:
    """Regression: the action stayed disabled after a run loaded.

    canExport reads the results controller, so it must be re-evaluated when
    that controller changes rather than only when the export controller does.
    """
    from PySide6.QtCore import QObject, Signal

    from variant_inference.qt.export_controller import ExportController

    class ResultsStub(QObject):
        stateChanged = Signal()

        def __init__(self) -> None:
            super().__init__()
            self.current_run = None

        def open(self, run) -> None:
            self.current_run = run
            self.stateChanged.emit()

    results = ResultsStub()
    controller = ExportController(ResearchExportService(CsvSourceReader()), results)
    notified: list[int] = []
    controller.stateChanged.connect(lambda: notified.append(1))

    assert controller.canExport is False

    results.open(run_for(write_source(tmp_path)))

    assert controller.canExport is True
    assert notified, "opening a run must notify the export action to re-evaluate"
