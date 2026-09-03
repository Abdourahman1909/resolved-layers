from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from variant_inference.domain.models import EvaluationCohort, EvaluationMetric


class EvaluationMetricModel(QAbstractListModel):
    KeyRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    DisplayRole = Qt.UserRole + 3
    DefinitionRole = Qt.UserRole + 4
    DefinedRole = Qt.UserRole + 5

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[EvaluationMetric, ...] = ()

    def set_items(self, items: tuple[EvaluationMetric, ...]) -> None:
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
            self.LabelRole: item.label,
            self.DisplayRole: item.display,
            self.DefinitionRole: item.definition,
            self.DefinedRole: item.value is not None,
        }
        return values.get(role)

    def roleNames(self):  # noqa: N802
        return {
            self.KeyRole: b"key",
            self.LabelRole: b"label",
            self.DisplayRole: b"display",
            self.DefinitionRole: b"definition",
            self.DefinedRole: b"defined",
        }


class EvaluationCohortModel(QAbstractListModel):
    KeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    DetailRole = Qt.UserRole + 3
    CountRole = Qt.UserRole + 4

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[EvaluationCohort, ...] = ()

    def set_items(self, items: tuple[EvaluationCohort, ...]) -> None:
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
