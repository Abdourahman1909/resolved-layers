from __future__ import annotations

import hashlib

import pytest

from variant_inference.infrastructure.csv_source import CsvSourceError, CsvSourceReader


def test_csv_identity_checksum_and_source_rows(tmp_path):
    raw = b"Variant_ID;score;note\nVAR-001;0.75;alpha\nVAR-002;;beta\n"
    path = tmp_path / "source.csv"
    path.write_bytes(raw)

    source = CsvSourceReader().open(path)
    try:
        assert source.identity.file_name == "source.csv"
        assert source.identity.row_count == 2
        assert source.identity.column_count == 3
        assert source.identity.sha256 == hashlib.sha256(raw).hexdigest()
        assert source.identity.delimiter == "Semicolon (;)"
        assert source.identity.encoding == "UTF-8"
        assert source.columns == ("Variant_ID", "score", "note")
        assert source.column_types == ("text", "number", "text")
        assert source.row_at(0) == ("VAR-001", "0.75", "alpha")
        assert source.row_at(1) == ("VAR-002", "", "beta")
    finally:
        database_path = source._database_path
        source.close()
    assert not database_path.exists()


def test_large_csv_uses_bounded_page_cache(tmp_path):
    path = tmp_path / "ten-thousand.csv"
    lines = ["id,a,b,c,d"] + [f"ROW-{index},{index},x,{index / 10}," for index in range(10_000)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    source = CsvSourceReader().open(path)
    try:
        assert source.identity.row_count == 10_000
        assert source.row_at(9_999)[0] == "ROW-9999"
        for index in range(0, 10_000, 128):
            source.row_at(index)
        assert sum(len(page) for page in source._pages.values()) <= source.cached_row_capacity
    finally:
        source.close()


def test_empty_csv_is_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")
    with pytest.raises(CsvSourceError, match="empty"):
        CsvSourceReader().open(path)

