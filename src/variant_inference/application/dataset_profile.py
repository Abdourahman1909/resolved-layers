from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from variant_inference.application.ports import SourceDataset
from variant_inference.domain.models import (
    GroundTruthAuthorization,
    GroupBreakdown,
    LabelCoverage,
    SourceValueFilter,
    SourceValueFilterMode,
)


MISSING_GROUP_VALUE = ""


@dataclass
class DatasetProfileSession:
    """Descriptive profile state over one immutable Source Dataset."""

    source: SourceDataset | None = None
    context_columns: tuple[str, ...] = ()
    group_columns: tuple[str, ...] = ()
    label_columns: tuple[str, ...] = ()
    group_column: str = ""
    label_column: str = ""
    authorization: GroundTruthAuthorization | None = None
    class_filter: str = ""
    group_filter: str | None = None
    _counts: dict[str, tuple[tuple[str, int], ...]] = field(default_factory=dict)

    def load_source(self, source: SourceDataset, context_columns: Sequence[str]) -> None:
        self.source = source
        source_names = set(source.columns)
        self.context_columns = tuple(
            dict.fromkeys(name for name in context_columns if name in source_names)
        )
        self._counts.clear()
        suitable = tuple(name for name in self.context_columns if self._is_suitable_category(name))
        self.group_columns = suitable
        self.label_columns = suitable
        self.group_column = "_panel" if "_panel" in suitable else (suitable[0] if suitable else "")
        self.label_column = ""
        self.authorization = None
        self.class_filter = ""
        self.group_filter = None

    def select_group_column(self, column_name: str) -> None:
        if column_name not in self.group_columns:
            raise ValueError(f"{column_name!r} is not a suitable Context Column for grouping.")
        if column_name != self.group_column:
            self.group_column = column_name
            self.group_filter = None

    def select_label_column(self, column_name: str) -> None:
        if column_name and column_name not in self.label_columns:
            raise ValueError(f"{column_name!r} is not available for Ground-Truth Authorization.")
        if column_name != self.label_column:
            self.label_column = column_name
            self.authorization = None
            self.class_filter = ""

    @property
    def label_values(self) -> tuple[str, ...]:
        if not self.label_column:
            return ()
        return tuple(value for value, _ in self._value_counts(self.label_column) if value)

    def authorize_labels(self, pathogenic_value: str, benign_value: str) -> None:
        if not self.label_column:
            raise ValueError("Select the source label column first.")
        available = set(self.label_values)
        if pathogenic_value not in available or benign_value not in available:
            raise ValueError("Both mappings must use values present in the selected label column.")
        self.authorization = GroundTruthAuthorization(
            column_name=self.label_column,
            pathogenic_value=pathogenic_value,
            benign_value=benign_value,
        )
        self.class_filter = ""

    def clear_authorization(self) -> None:
        self.authorization = None
        self.class_filter = ""

    @property
    def label_coverage(self) -> LabelCoverage | None:
        if self.source is None or self.authorization is None:
            return None
        counts = dict(self._value_counts(self.authorization.column_name))
        pathogenic = counts.get(self.authorization.pathogenic_value, 0)
        benign = counts.get(self.authorization.benign_value, 0)
        missing = counts.get("", 0)
        unrecognized = self.source.identity.row_count - pathogenic - benign - missing
        return LabelCoverage(
            total=self.source.identity.row_count,
            pathogenic=pathogenic,
            benign=benign,
            missing=missing,
            unrecognized=unrecognized,
        )

    @property
    def groups(self) -> tuple[GroupBreakdown, ...]:
        if self.source is None or not self.group_column:
            return ()
        total_rows = self.source.identity.row_count
        group_counts = self._value_counts(self.group_column)
        label_by_group: dict[tuple[str, str], int] = {}
        if self.authorization is not None:
            group_index = self.source.columns.index(self.group_column)
            label_index = self.source.columns.index(self.authorization.column_name)
            label_by_group = {
                (group, label): count
                for group, label, count in self.source.paired_value_counts(group_index, label_index)
            }
        entries = []
        for group, count in group_counts:
            pathogenic = 0
            benign = 0
            invalid = 0
            if self.authorization is not None:
                pathogenic = label_by_group.get(
                    (group, self.authorization.pathogenic_value), 0
                )
                benign = label_by_group.get((group, self.authorization.benign_value), 0)
                invalid = count - pathogenic - benign
            entries.append(
                GroupBreakdown(
                    value=group,
                    total=count,
                    share=(count / total_rows) if total_rows else 0.0,
                    pathogenic=pathogenic,
                    benign=benign,
                    missing_or_unrecognized=invalid,
                )
            )
        return tuple(entries)

    def set_class_filter(self, class_name: str) -> None:
        if class_name and self.authorization is None:
            raise ValueError("Class filters require authorized source labels.")
        if class_name not in {"", "pathogenic", "benign", "missing", "unrecognized"}:
            raise ValueError(f"Unknown class filter: {class_name}")
        self.class_filter = class_name

    def set_group_filter(self, value: str | None) -> None:
        if value is not None and not self.group_column:
            raise ValueError("Group filtering requires a selected Context Column.")
        self.group_filter = value

    @property
    def active_filters(self) -> tuple[tuple[str, str], ...]:
        filters: list[tuple[str, str]] = []
        if self.class_filter:
            filters.append(("class", self.class_filter.capitalize()))
        if self.group_filter is not None:
            label = self.group_filter if self.group_filter else "Missing"
            filters.append(("group", f"{self.group_column}: {label}"))
        return tuple(filters)

    @property
    def filtered_source_rows(self) -> tuple[int, ...] | None:
        if self.source is None:
            return None
        filters: list[SourceValueFilter] = []
        if self.group_filter is not None:
            filters.append(
                self._value_filter(self.group_column, self.group_filter)
            )
        if self.class_filter and self.authorization is not None:
            column_index = self.source.columns.index(self.authorization.column_name)
            if self.class_filter == "pathogenic":
                filters.append(
                    SourceValueFilter(
                        column_index,
                        SourceValueFilterMode.EXACT,
                        value=self.authorization.pathogenic_value,
                    )
                )
            elif self.class_filter == "benign":
                filters.append(
                    SourceValueFilter(
                        column_index,
                        SourceValueFilterMode.EXACT,
                        value=self.authorization.benign_value,
                    )
                )
            elif self.class_filter == "missing":
                filters.append(SourceValueFilter(column_index, SourceValueFilterMode.MISSING))
            else:
                filters.append(
                    SourceValueFilter(
                        column_index,
                        SourceValueFilterMode.UNRECOGNIZED,
                        recognized_values=(
                            self.authorization.pathogenic_value,
                            self.authorization.benign_value,
                        ),
                    )
                )
        return self.source.matching_source_rows(filters) if filters else None

    def _value_filter(self, column_name: str, value: str) -> SourceValueFilter:
        assert self.source is not None
        column_index = self.source.columns.index(column_name)
        if value == MISSING_GROUP_VALUE:
            return SourceValueFilter(column_index, SourceValueFilterMode.MISSING)
        return SourceValueFilter(column_index, SourceValueFilterMode.EXACT, value=value)

    def _value_counts(self, column_name: str) -> tuple[tuple[str, int], ...]:
        if self.source is None:
            return ()
        if column_name not in self._counts:
            self._counts[column_name] = self.source.value_counts(
                self.source.columns.index(column_name)
            )
        return self._counts[column_name]

    def _is_suitable_category(self, column_name: str) -> bool:
        if self.source is None:
            return False
        counts = self._value_counts(column_name)
        distinct_non_missing = sum(1 for value, _ in counts if value)
        maximum = min(100, max(12, self.source.identity.row_count // 5))
        return 1 <= distinct_non_missing <= maximum
