from __future__ import annotations

from variant_inference.application.dataset_profile import DatasetProfileSession
from variant_inference.domain.models import SourceValueFilter, SourceValueFilterMode
from variant_inference.infrastructure.csv_source import CsvSourceReader


def test_profile_requires_explicit_label_mapping_and_preserves_coverage(fixture_dir):
    source = CsvSourceReader().open(fixture_dir / "dataset_profile.csv")
    try:
        profile = DatasetProfileSession()
        profile.load_source(
            source,
            ("_panel", "Study", "Reference_Label", "Research_Note"),
        )

        assert profile.group_column == "_panel"
        assert profile.authorization is None
        assert profile.label_coverage is None

        profile.select_label_column("Reference_Label")
        assert set(profile.label_values) == {"case", "control", "pending", "review"}
        profile.authorize_labels("case", "control")

        coverage = profile.label_coverage
        assert coverage is not None
        assert (coverage.pathogenic, coverage.benign) == (5, 4)
        assert (coverage.missing, coverage.unrecognized, coverage.recognized) == (1, 2, 9)
    finally:
        source.close()


def test_group_and_class_filters_resolve_exact_source_rows(fixture_dir):
    source = CsvSourceReader().open(fixture_dir / "dataset_profile.csv")
    try:
        profile = DatasetProfileSession()
        profile.load_source(source, ("_panel", "Study", "Reference_Label"))
        profile.select_label_column("Reference_Label")
        profile.authorize_labels("case", "control")

        groups = {entry.value: entry for entry in profile.groups}
        assert groups["Cohort-A"].total == 5
        assert groups["Cohort-A"].pathogenic == 3
        assert groups["Cohort-A"].benign == 1
        assert groups["Cohort-A"].missing_or_unrecognized == 1

        profile.set_group_filter("Cohort-A")
        profile.set_class_filter("pathogenic")
        assert profile.filtered_source_rows == (1, 5, 11)
        assert profile.active_filters == (
            ("class", "Pathogenic"),
            ("group", "_panel: Cohort-A"),
        )
    finally:
        source.close()


def test_sql_profile_queries_keep_missing_and_unrecognized_distinct(fixture_dir):
    source = CsvSourceReader().open(fixture_dir / "dataset_profile.csv")
    try:
        label_index = source.columns.index("Reference_Label")
        counts = dict(source.value_counts(label_index))
        assert counts[""] == 1
        assert source.missing_cell_count == 3
        assert source.rows_with_missing == 3

        missing = source.matching_source_rows(
            (SourceValueFilter(label_index, SourceValueFilterMode.MISSING),)
        )
        unrecognized = source.matching_source_rows(
            (
                SourceValueFilter(
                    label_index,
                    SourceValueFilterMode.UNRECOGNIZED,
                    recognized_values=("case", "control"),
                ),
            )
        )
        assert missing == (6,)
        assert unrecognized == (7, 10)
    finally:
        source.close()


def test_ten_thousand_row_profile_aggregates_and_filters_in_sql(tmp_path):
    path = tmp_path / "ten-thousand-profile.csv"
    rows = ["Record_ID,_panel,Reference_Label,measurement"]
    rows.extend(
        f"SYN-{index:05d},Group-{index % 5},{'case' if index % 2 == 0 else 'control'},{index / 10}"
        for index in range(10_000)
    )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    source = CsvSourceReader().open(path)
    try:
        profile = DatasetProfileSession()
        profile.load_source(source, ("_panel", "Reference_Label"))
        profile.select_label_column("Reference_Label")
        profile.authorize_labels("case", "control")
        profile.set_group_filter("Group-2")
        profile.set_class_filter("pathogenic")

        assert len(profile.groups) == 5
        assert len(profile.filtered_source_rows or ()) == 1_000
        assert not source._pages
    finally:
        source.close()
