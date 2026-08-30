from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QAbstractTableModel, QModelIndex, Qt, Slot

from variant_inference.domain.models import (
    InvestigationSet,
    PredictionRecord,
    RunArchiveEntry,
    ScoreBin,
    SourceFieldEvidence,
)


class PredictionTableModel(QAbstractTableModel):
    SourceRowRole = Qt.UserRole + 1
    ColumnLabelRole = Qt.UserRole + 2

    HEADERS = (
        "Source Row",
        "Prediction",
        "Ensemble Score",
        "CatBoost",
        "LightGBM",
        "Model Disagreement",
    )

    def __init__(self) -> None:
        super().__init__()
        self._records: tuple[PredictionRecord, ...] = ()
        self._visible: tuple[PredictionRecord, ...] = ()
        self._query = ""

    def set_records(self, records: tuple[PredictionRecord, ...]) -> None:
        self.beginResetModel()
        self._records = records
        self._visible = self._apply_query(records, self._query)
        self.endResetModel()

    @property
    def visible_count(self) -> int:
        return len(self._visible)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._visible)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        record = self._visible[index.row()]
        if role == self.SourceRowRole:
            return record.source_row
        if role == self.ColumnLabelRole:
            return self.HEADERS[index.column()]
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        component_scores = record.component_scores
        values = (
            record.source_row,
            record.prediction,
            f"{record.ensemble_score:.6f}",
            f"{component_scores.get('catboost', 0.0):.6f}",
            f"{component_scores.get('lightgbm', 0.0):.6f}",
            f"{record.model_disagreement:.6f}",
        )
        return values[index.column()]

    def roleNames(self):  # noqa: N802
        return {
            Qt.DisplayRole: b"display",
            self.SourceRowRole: b"sourceRow",
            self.ColumnLabelRole: b"columnLabel",
        }

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return self.HEADERS[section]

    @Slot(str)
    def set_search(self, query: str) -> None:
        self.beginResetModel()
        self._query = query.strip().casefold()
        self._visible = self._apply_query(self._records, self._query)
        self.endResetModel()

    def record_at(self, visible_row: int) -> PredictionRecord:
        if not 0 <= visible_row < len(self._visible):
            raise IndexError(visible_row)
        return self._visible[visible_row]

    def visible_index_for_source_row(self, source_row: int) -> int:
        return next(
            (
                index
                for index, record in enumerate(self._visible)
                if record.source_row == source_row
            ),
            -1,
        )

    @staticmethod
    def _apply_query(
        records: tuple[PredictionRecord, ...], query: str
    ) -> tuple[PredictionRecord, ...]:
        if not query:
            return records
        return tuple(
            record
            for record in records
            if query in str(record.source_row).casefold()
            or query in record.prediction.casefold()
        )


class ScoreHistogramModel(QAbstractListModel):
    LowerRole = Qt.UserRole + 1
    UpperRole = Qt.UserRole + 2
    CountRole = Qt.UserRole + 3
    HeightRole = Qt.UserRole + 4

    def __init__(self) -> None:
        super().__init__()
        self._bins: tuple[ScoreBin, ...] = ()

    def set_bins(self, bins: tuple[ScoreBin, ...]) -> None:
        self.beginResetModel()
        self._bins = bins
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._bins)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._bins[index.row()]
        maximum = max((value.count for value in self._bins), default=1)
        values = {
            self.LowerRole: item.lower,
            self.UpperRole: item.upper,
            self.CountRole: item.count,
            self.HeightRole: item.count / maximum if maximum else 0.0,
        }
        return values.get(role)

    def roleNames(self):  # noqa: N802
        return {
            self.LowerRole: b"lower",
            self.UpperRole: b"upper",
            self.CountRole: b"count",
            self.HeightRole: b"heightRatio",
        }


class SourceFieldListModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    ValueRole = Qt.UserRole + 2
    ValueTypeRole = Qt.UserRole + 3

    def __init__(self) -> None:
        super().__init__()
        self._fields: tuple[SourceFieldEvidence, ...] = ()
        self._visible: tuple[SourceFieldEvidence, ...] = ()
        self._query = ""

    def set_fields(self, fields: tuple[SourceFieldEvidence, ...]) -> None:
        self.beginResetModel()
        self._fields = fields
        self._visible = self._apply_query(fields, self._query)
        self.endResetModel()

    @property
    def total_count(self) -> int:
        return len(self._fields)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._visible)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        field = self._visible[index.row()]
        values = {
            Qt.DisplayRole: field.value,
            self.NameRole: field.name,
            self.ValueRole: field.value,
            self.ValueTypeRole: field.value_type,
        }
        return values.get(role)

    def set_search(self, query: str) -> None:
        self.beginResetModel()
        self._query = query.strip().casefold()
        self._visible = self._apply_query(self._fields, self._query)
        self.endResetModel()

    @staticmethod
    def _apply_query(
        fields: tuple[SourceFieldEvidence, ...], query: str
    ) -> tuple[SourceFieldEvidence, ...]:
        if not query:
            return fields
        return tuple(
            field
            for field in fields
            if query in field.name.casefold()
            or query in field.value.casefold()
            or query in field.value_type.casefold()
        )

    def roleNames(self):  # noqa: N802
        return {
            self.NameRole: b"fieldName",
            self.ValueRole: b"fieldValue",
            self.ValueTypeRole: b"fieldType",
        }


class InvestigationSetModel(QAbstractListModel):
    KeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    DetailRole = Qt.UserRole + 3
    CountRole = Qt.UserRole + 4

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[InvestigationSet, ...] = ()

    def set_items(self, items: tuple[InvestigationSet, ...]) -> None:
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        values = {
            self.KeyRole: item.key,
            self.TitleRole: item.title,
            self.DetailRole: item.detail,
            self.CountRole: item.count,
        }
        return values.get(role)

    def roleNames(self):  # noqa: N802
        return {
            self.KeyRole: b"key",
            self.TitleRole: b"title",
            self.DetailRole: b"detail",
            self.CountRole: b"count",
        }


class RunArchiveListModel(QAbstractListModel):
    RunIdRole = Qt.UserRole + 1
    CompletedAtRole = Qt.UserRole + 2
    SourceNameRole = Qt.UserRole + 3
    PackageNameRole = Qt.UserRole + 4
    PackageVersionRole = Qt.UserRole + 5
    RecordCountRole = Qt.UserRole + 6
    PathogenicCountRole = Qt.UserRole + 7
    WarningCountRole = Qt.UserRole + 8

    def __init__(self) -> None:
        super().__init__()
        self._entries: tuple[RunArchiveEntry, ...] = ()

    def set_entries(self, entries: tuple[RunArchiveEntry, ...]) -> None:
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._entries[index.row()]
        values = {
            self.RunIdRole: item.run_id,
            self.CompletedAtRole: item.completed_at,
            self.SourceNameRole: item.source_file_name,
            self.PackageNameRole: item.model_package_name,
            self.PackageVersionRole: item.model_package_version,
            self.RecordCountRole: item.record_count,
            self.PathogenicCountRole: item.pathogenic_count,
            self.WarningCountRole: item.warning_count,
        }
        return values.get(role)

    def roleNames(self):  # noqa: N802
        return {
            self.RunIdRole: b"runId",
            self.CompletedAtRole: b"completedAt",
            self.SourceNameRole: b"sourceName",
            self.PackageNameRole: b"packageName",
            self.PackageVersionRole: b"packageVersion",
            self.RecordCountRole: b"recordCount",
            self.PathogenicCountRole: b"pathogenicCount",
            self.WarningCountRole: b"warningCount",
        }
