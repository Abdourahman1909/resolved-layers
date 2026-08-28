from __future__ import annotations

import codecs
import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from variant_inference.domain.models import SourceIdentity, SourceValueFilter, SourceValueFilterMode


class CsvSourceError(ValueError):
    pass


class CsvSource:
    """Read-only, disk-backed Source Dataset with a bounded row-page cache."""

    PAGE_SIZE = 128
    MAX_CACHED_PAGES = 8

    def __init__(
        self,
        identity: SourceIdentity,
        columns: tuple[str, ...],
        column_types: tuple[str, ...],
        database_path: Path,
        connection: sqlite3.Connection,
        missing_cell_count: int,
        rows_with_missing: int,
    ) -> None:
        self.identity = identity
        self.columns = columns
        self.column_types = column_types
        self._database_path = database_path
        self._connection = connection
        self.missing_cell_count = missing_cell_count
        self.rows_with_missing = rows_with_missing
        self._pages: OrderedDict[int, tuple[tuple[str, ...], ...]] = OrderedDict()
        self._closed = False

    @property
    def cached_row_capacity(self) -> int:
        return self.PAGE_SIZE * self.MAX_CACHED_PAGES

    def row_at(self, source_row_index: int) -> tuple[str, ...]:
        if self._closed:
            raise RuntimeError("Source Dataset is closed.")
        if not 0 <= source_row_index < self.identity.row_count:
            raise IndexError(source_row_index)
        page_number = source_row_index // self.PAGE_SIZE
        if page_number not in self._pages:
            self._load_page(page_number)
        page = self._pages.pop(page_number)
        self._pages[page_number] = page
        return page[source_row_index % self.PAGE_SIZE]

    def value_counts(self, column_index: int) -> tuple[tuple[str, int], ...]:
        self._validate_column_index(column_index)
        path = f"$[{column_index}]"
        expression = (
            "CASE WHEN TRIM(COALESCE(CAST(json_extract(payload, ?) AS TEXT), '')) = '' "
            "THEN '' ELSE CAST(json_extract(payload, ?) AS TEXT) END"
        )
        records = self._connection.execute(
            f"SELECT {expression} AS source_value, COUNT(*) "
            "FROM source_rows GROUP BY source_value "
            "ORDER BY COUNT(*) DESC, source_value COLLATE NOCASE",
            (path, path),
        ).fetchall()
        return tuple((str(value or ""), int(count)) for value, count in records)

    def paired_value_counts(
        self, first_column_index: int, second_column_index: int
    ) -> tuple[tuple[str, str, int], ...]:
        self._validate_column_index(first_column_index)
        self._validate_column_index(second_column_index)
        first_path = f"$[{first_column_index}]"
        second_path = f"$[{second_column_index}]"
        expression = (
            "CASE WHEN TRIM(COALESCE(CAST(json_extract(payload, ?) AS TEXT), '')) = '' "
            "THEN '' ELSE CAST(json_extract(payload, ?) AS TEXT) END"
        )
        records = self._connection.execute(
            f"SELECT {expression} AS first_value, {expression} AS second_value, COUNT(*) "
            "FROM source_rows GROUP BY first_value, second_value "
            "ORDER BY first_value COLLATE NOCASE, second_value COLLATE NOCASE",
            (first_path, first_path, second_path, second_path),
        ).fetchall()
        return tuple(
            (str(first or ""), str(second or ""), int(count))
            for first, second, count in records
        )

    def matching_source_rows(self, filters: Iterable[SourceValueFilter]) -> tuple[int, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        for item in filters:
            self._validate_column_index(item.column_index)
            path = f"$[{item.column_index}]"
            value_expression = "CAST(json_extract(payload, ?) AS TEXT)"
            if item.mode is SourceValueFilterMode.EXACT:
                clauses.append(f"{value_expression} = ?")
                parameters.extend((path, item.value))
            elif item.mode is SourceValueFilterMode.MISSING:
                clauses.append(
                    "TRIM(COALESCE(CAST(json_extract(payload, ?) AS TEXT), '')) = ''"
                )
                parameters.append(path)
            elif item.mode is SourceValueFilterMode.UNRECOGNIZED:
                placeholders = ", ".join("?" for _ in item.recognized_values)
                clause = (
                    "TRIM(COALESCE(CAST(json_extract(payload, ?) AS TEXT), '')) != ''"
                )
                parameters.append(path)
                if placeholders:
                    clause += f" AND {value_expression} NOT IN ({placeholders})"
                    parameters.append(path)
                    parameters.extend(item.recognized_values)
                clauses.append(f"({clause})")
            else:  # pragma: no cover - exhaustive enum guard
                raise ValueError(f"Unsupported Source Value filter: {item.mode}")
        query = "SELECT source_row FROM source_rows"
        if clauses:
            query += " WHERE " + " AND ".join(f"({clause})" for clause in clauses)
        query += " ORDER BY source_row"
        return tuple(int(row[0]) for row in self._connection.execute(query, parameters))

    def _load_page(self, page_number: int) -> None:
        first_row = page_number * self.PAGE_SIZE + 1
        last_row = first_row + self.PAGE_SIZE
        records = self._connection.execute(
            "SELECT source_row, payload FROM source_rows WHERE source_row >= ? AND source_row < ? ORDER BY source_row",
            (first_row, last_row),
        ).fetchall()
        page = tuple(tuple(str(value) for value in json.loads(payload)) for _, payload in records)
        self._pages[page_number] = page
        while len(self._pages) > self.MAX_CACHED_PAGES:
            self._pages.popitem(last=False)

    def _validate_column_index(self, column_index: int) -> None:
        if self._closed:
            raise RuntimeError("Source Dataset is closed.")
        if not 0 <= column_index < len(self.columns):
            raise IndexError(column_index)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._pages.clear()
        self._connection.close()
        try:
            self._database_path.unlink(missing_ok=True)
        except OSError:
            pass

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class CsvSourceReader:
    SAMPLE_BYTES = 128 * 1024
    TYPE_SAMPLE_ROWS = 256

    def open(self, path: Path) -> CsvSource:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise CsvSourceError(f"CSV file not found: {path}")

        encoding = self._detect_encoding(path)
        delimiter = self._detect_delimiter(path, encoding)
        checksum = self._sha256(path)
        stat = path.stat()
        database_file = tempfile.NamedTemporaryFile(prefix="chl-source-review-", suffix=".sqlite3", delete=False)
        database_path = Path(database_file.name)
        database_file.close()
        connection = sqlite3.connect(database_path)

        try:
            connection.execute(
                "CREATE TABLE source_rows (source_row INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
            )
            columns, row_count, samples, missing_cell_count, rows_with_missing = self._scan_into_store(
                path, encoding, delimiter, connection
            )
            column_types = self._infer_types(samples, len(columns))
            identity = SourceIdentity(
                path=path,
                file_name=path.name,
                row_count=row_count,
                column_count=len(columns),
                sha256=checksum,
                delimiter=self._delimiter_label(delimiter),
                encoding=encoding.upper().replace("-SIG", " with BOM"),
                last_modified=datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            )
            return CsvSource(
                identity,
                columns,
                column_types,
                database_path,
                connection,
                missing_cell_count,
                rows_with_missing,
            )
        except Exception:
            connection.close()
            database_path.unlink(missing_ok=True)
            raise

    def _scan_into_store(
        self,
        path: Path,
        encoding: str,
        delimiter: str,
        connection: sqlite3.Connection,
    ) -> tuple[tuple[str, ...], int, list[tuple[str, ...]], int, int]:
        samples: list[tuple[str, ...]] = []
        batch: list[tuple[int, str]] = []
        missing_cell_count = 0
        rows_with_missing = 0
        with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            try:
                header = next(reader)
            except StopIteration as error:
                raise CsvSourceError("The selected CSV is empty.") from error
            columns = tuple(value.strip() for value in header)
            if not columns or all(not value for value in columns):
                raise CsvSourceError("The selected CSV does not contain a header row.")
            if any(not value for value in columns):
                raise CsvSourceError("Every source column must have a non-empty name.")

            row_count = 0
            for row_count, raw_row in enumerate(reader, start=1):
                if len(raw_row) > len(columns):
                    raise CsvSourceError(
                        f"Source Row {row_count} contains {len(raw_row)} values for {len(columns)} columns."
                    )
                row = tuple(raw_row) + ("",) * (len(columns) - len(raw_row))
                row_missing_count = sum(1 for value in row if not value.strip())
                missing_cell_count += row_missing_count
                rows_with_missing += int(row_missing_count > 0)
                if len(samples) < self.TYPE_SAMPLE_ROWS:
                    samples.append(row)
                batch.append((row_count, json.dumps(row, ensure_ascii=False, separators=(",", ":"))))
                if len(batch) >= 500:
                    connection.executemany("INSERT INTO source_rows VALUES (?, ?)", batch)
                    batch.clear()
            if batch:
                connection.executemany("INSERT INTO source_rows VALUES (?, ?)", batch)
            connection.commit()
        return columns, row_count, samples, missing_cell_count, rows_with_missing

    def _detect_encoding(self, path: Path) -> str:
        with path.open("rb") as handle:
            if handle.read(3) == codecs.BOM_UTF8:
                return "utf-8-sig"
        decoder = codecs.getincrementaldecoder("utf-8")("strict")
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    decoder.decode(chunk)
                decoder.decode(b"", final=True)
            return "utf-8"
        except UnicodeDecodeError:
            return "cp1252"

    def _detect_delimiter(self, path: Path, encoding: str) -> str:
        with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
            sample = handle.read(self.SAMPLE_BYTES)
        try:
            return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            return ","

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _infer_types(
        self, samples: Iterable[tuple[str, ...]], column_count: int
    ) -> tuple[str, ...]:
        observations: list[set[str]] = [set() for _ in range(column_count)]
        for row in samples:
            for index, value in enumerate(row):
                text = value.strip()
                if not text:
                    continue
                try:
                    int(text)
                    observations[index].add("integer")
                    continue
                except ValueError:
                    pass
                try:
                    float(text)
                    observations[index].add("number")
                except ValueError:
                    observations[index].add("text")
        labels = []
        for kinds in observations:
            if not kinds:
                labels.append("empty")
            elif kinds <= {"integer"}:
                labels.append("integer")
            elif kinds <= {"integer", "number"}:
                labels.append("number")
            elif kinds == {"text"}:
                labels.append("text")
            else:
                labels.append("mixed")
        return tuple(labels)

    def _delimiter_label(self, delimiter: str) -> str:
        names = {",": "Comma (,)", ";": "Semicolon (;)", "\t": "Tab", "|": "Pipe (|)"}
        return names.get(delimiter, repr(delimiter))
