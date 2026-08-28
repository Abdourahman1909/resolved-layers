from __future__ import annotations

from PySide6.QtCore import Qt

from variant_inference.infrastructure.model_package import JsonModelPackageRepository
from variant_inference.qt.controller import SourceReviewController
from variant_inference.qt.profile_model import GroupBreakdownModel
from variant_inference.qt.table_model import CsvTableModel


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

        controller.selectLabelColumn("Reference_Label")
        controller.authorizeLabels("case", "control")
        controller.setGroupFilter("Cohort-A")
        controller.setClassFilter("pathogenic")

        assert controller.labelsAuthorized
        assert controller.filteredRowCount == 3
        assert table.data(table.index(0, 0), Qt.DisplayRole) == 1
        assert table.data(table.index(1, 0), Qt.DisplayRole) == 5
        assert table.data(table.index(2, 0), Qt.DisplayRole) == 11
    finally:
        controller.close()
