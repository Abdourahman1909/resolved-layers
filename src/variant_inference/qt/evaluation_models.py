from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from variant_inference.domain.models import (
    EvaluationCohort,
    EvaluationGroup,
    EvaluationMetric,
)


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


class EvaluationGroupModel(QAbstractListModel):
    """One row per group value, with its own confusion counts and metrics.

    The competition combines panels by weighting each equally, so the per-group
    figures matter independently of the pooled cohort.
    """

    ValueRole = Qt.UserRole + 1
    EvaluatedRole = Qt.UserRole + 2
    TruePositiveRole = Qt.UserRole + 3
    FalsePositiveRole = Qt.UserRole + 4
    FalseNegativeRole = Qt.UserRole + 5
    TrueNegativeRole = Qt.UserRole + 6
    F1Role = Qt.UserRole + 7
    MccRole = Qt.UserRole + 8
    PrecisionRole = Qt.UserRole + 9
    RecallRole = Qt.UserRole + 10

    def __init__(self) -> None:
        super().__init__()
        self._items: tuple[EvaluationGroup, ...] = ()

    def set_items(self, items: tuple[EvaluationGroup, ...]) -> None:
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
            self.ValueRole: item.value,
            self.EvaluatedRole: item.evaluated_count,
            self.TruePositiveRole: item.true_positive,
            self.FalsePositiveRole: item.false_positive,
            self.FalseNegativeRole: item.false_negative,
            self.TrueNegativeRole: item.true_negative,
            self.F1Role: item.metric("f1").display,
            self.MccRole: item.metric("mcc").display,
            self.PrecisionRole: item.metric("precision").display,
            self.RecallRole: item.metric("recall").display,
        }
        return values.get(role)

    def roleNames(self):  # noqa: N802
        return {
            self.ValueRole: b"groupValue",
            self.EvaluatedRole: b"evaluated",
            self.TruePositiveRole: b"truePositive",
            self.FalsePositiveRole: b"falsePositive",
            self.FalseNegativeRole: b"falseNegative",
            self.TrueNegativeRole: b"trueNegative",
            self.F1Role: b"f1",
            self.MccRole: b"mcc",
            self.PrecisionRole: b"precision",
            self.RecallRole: b"recall",
        }
