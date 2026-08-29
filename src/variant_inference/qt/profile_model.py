from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from variant_inference.domain.models import GroupBreakdown


class GroupBreakdownModel(QAbstractListModel):
    ValueRole = Qt.UserRole + 1
    DisplayValueRole = Qt.UserRole + 2
    TotalRole = Qt.UserRole + 3
    ShareRole = Qt.UserRole + 4
    ShareTextRole = Qt.UserRole + 5
    PathogenicRole = Qt.UserRole + 6
    BenignRole = Qt.UserRole + 7
    InvalidRole = Qt.UserRole + 8
    HasLabelsRole = Qt.UserRole + 9

    def __init__(self) -> None:
        super().__init__()
        self._groups: tuple[GroupBreakdown, ...] = ()
        self._has_labels = False

    def set_groups(self, groups: tuple[GroupBreakdown, ...], has_labels: bool) -> None:
        self.beginResetModel()
        self._groups = groups
        self._has_labels = has_labels
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._groups)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._groups):
            return None
        entry = self._groups[index.row()]
        values = {
            self.ValueRole: entry.value,
            self.DisplayValueRole: entry.value if entry.value else "Missing",
            self.TotalRole: entry.total,
            self.ShareRole: entry.share,
            self.ShareTextRole: f"{entry.share * 100:.1f}%",
            self.PathogenicRole: entry.pathogenic,
            self.BenignRole: entry.benign,
            self.InvalidRole: entry.missing_or_unrecognized,
            self.HasLabelsRole: self._has_labels,
        }
        return values.get(role)

    def roleNames(self):  # noqa: N802
        return {
            self.ValueRole: b"value",
            self.DisplayValueRole: b"displayValue",
            self.TotalRole: b"total",
            self.ShareRole: b"share",
            self.ShareTextRole: b"shareText",
            self.PathogenicRole: b"pathogenic",
            self.BenignRole: b"benign",
            self.InvalidRole: b"invalid",
            self.HasLabelsRole: b"hasLabels",
        }
