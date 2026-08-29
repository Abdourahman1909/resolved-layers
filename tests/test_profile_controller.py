from __future__ import annotations

from PySide6.QtCore import Qt

from variant_inference.domain.models import ArchivedRun
from variant_inference.infrastructure.model_package import JsonModelPackageRepository
from variant_inference.qt.controller import SourceReviewController
from variant_inference.qt.profile_model import GroupBreakdownModel
from variant_inference.qt.table_model import CsvTableModel


class StubVerifiedRuns:
    def __init__(self, root):
        self.root = root
        self.called = False

    def execute(self, **values):
        self.called = True
        assert values["operator_confirmed"]
        return ArchivedRun(
            run_id="run-controller-test",
            directory=self.root / "run-controller-test",
            manifest_path=self.root / "run-controller-test" / "manifest.json",
            predictions_path=self.root / "run-controller-test" / "predictions.jsonl",
        )


def test_profile_controller_filters_shared_table_without_rewriting_source_row(fixture_dir):
    package = JsonModelPackageRepository().load(
        fixture_dir / "development-package" / "manifest.json"
    )
    table = CsvTableModel()
    controller = SourceReviewController(table, GroupBreakdownModel(), package)
    try:
        controller.openSource(str(fixture_dir / "dataset_profile.csv"))
        assert controller.groupColumn == "_panel"
        assert not controller.labelsAuthorized
        controller.setActiveSurface("profile")

        controller.selectLabelColumn("Reference_Label")
        controller.authorizeLabels("case", "control")
        controller.setGroupFilter("Cohort-A")
        controller.setClassFilter("pathogenic")

        assert controller.labelsAuthorized
        assert controller.filteredRowCount == 3
        assert table.data(table.index(0, 0), Qt.DisplayRole) == 1
        assert table.data(table.index(1, 0), Qt.DisplayRole) == 5
        assert table.data(table.index(2, 0), Qt.DisplayRole) == 11

        controller.setActiveSurface("review")
        assert table.rowCount() == 12
        controller.setActiveSurface("profile")
        assert table.rowCount() == 3
    finally:
        controller.close()


def test_controller_creates_verified_run_only_after_confirmation(fixture_dir, tmp_path):
    package = JsonModelPackageRepository().load(
        fixture_dir / "development-package" / "manifest.json"
    )
    verified_runs = StubVerifiedRuns(tmp_path)
    controller = SourceReviewController(
        CsvTableModel(),
        GroupBreakdownModel(),
        package,
        verified_runs=verified_runs,
    )
    try:
        controller.openSource(str(fixture_dir / "dataset_profile.csv"))
        assert not controller.runEnabled
        controller.requestRun()
        assert not verified_runs.called

        controller.setConfirmed(True)
        assert controller.runEnabled
        controller.requestRun()

        assert verified_runs.called
        assert controller.lastRunId == "run-controller-test"
        assert controller.lastRunPath.endswith("run-controller-test")
        assert controller.statusKind == "success"
    finally:
        controller.close()
