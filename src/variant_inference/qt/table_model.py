from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Slot

from variant_inference.application.ports import SourceDataset


class CsvTableModel(QAbstractTableModel):
    """Virtualized bridge: QML creates only visible cells and rows load in bounded pages."""

    def __init__(self) -> None:
        super().__init__()
        self._source: SourceDataset | None = None
        self._visible_columns: list[int] = []
        self._source_rows: tuple[int, ...] | None = None

    def set_source(self, source: SourceDataset | None) -> None:
        self.beginResetModel()
        self._source = source
        self._visible_columns = list(range(len(source.columns))) if source else []
        self._source_rows = None
        self.endResetModel()

    def set_row_filter(self, source_rows: tuple[int, ...] | None) -> None:
        self.beginResetModel()
        self._source_rows = source_rows
        self.endResetModel()

    @property
    def filtered_row_count(self) -> int:
        if self._source is None:
            return 0
        return len(self._source_rows) if self._source_rows is not None else self._source.identity.row_count

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid() or self._source is None:
            return 0
        return self.filtered_row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid() or self._source is None:
            return 0
        return 1 + len(self._visible_columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or self._source is None or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        source_row = self._source_rows[index.row()] if self._source_rows is not None else index.row() + 1
        if index.column() == 0:
            return source_row
        source_column = self._visible_columns[index.column() - 1]
        value = self._source.row_at(source_row - 1)[source_column]
        return value if value != "" else "—"

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if role != Qt.DisplayRole or orientation != Qt.Horizontal or self._source is None:
            return None
        if section == 0:
            return "Source Row\n(original)"
        source_column = self._visible_columns[section - 1]
        return f"{self._source.columns[source_column]}\n({self._source.column_types[source_column]})"

    @Slot(str)
    def filter_columns(self, query: str) -> None:
        if self._source is None:
            return
        normalized = query.strip().casefold()
        visible = [
            index
            for index, name in enumerate(self._source.columns)
            if not normalized or normalized in name.casefold()
        ]
        self.beginResetModel()
        self._visible_columns = visible
        self.endResetModel()

    @Slot()
    def reset_columns(self) -> None:
        self.filter_columns("")
