from __future__ import annotations

import hashlib
from pathlib import Path

from variant_inference.application.variant_inspector import SourceRowEvidenceService
from variant_inference.domain.models import (
    LoadedVerifiedRun,
    PredictionRecord,
    SourceIdentity,
    SourceReferenceState,
    SourceReferenceStatus,
)
from variant_inference.infrastructure.csv_source import CsvSourceReader


def loaded_run(source_path: Path, source_sha256: str) -> LoadedVerifiedRun:
    predictions = (
        PredictionRecord(1, 0.2, "Benign", {"catboost": 0.18, "lightgbm": 0.22}, 0.02),
        PredictionRecord(2, 0.8, "Pathogenic", {"catboost": 0.78, "lightgbm": 0.82}, 0.02),
    )
    return LoadedVerifiedRun(
        run_id="run-inspector",
        created_at="2026-08-30T12:00:00+00:00",
        completed_at="2026-08-30T12:00:01+00:00",
        duration_ms=1000,
        source_path=source_path,
        source_file_name=source_path.name,
        source_sha256=source_sha256,
        source_row_count=2,
        source_column_count=3,
        model_package_name="CHL Ensemble",
        model_package_version="2026.1",
        model_package_manifest_checksum="1" * 64,
        inference_contract_id="contract",
        inference_contract_version="2026.1",
        inference_contract_checksum="2" * 64,
        release_threshold=0.61,
        predictions_sha256="3" * 64,
        predictions=predictions,
    )


class MemoryArchive:
    def __init__(self, status: SourceReferenceStatus) -> None:
        self.status = status
        self.source_status_calls = 0

    def source_status(self, run_id: str) -> SourceReferenceStatus:
        assert run_id == "run-inspector"
        self.source_status_calls += 1
        return self.status


class MemorySource:
    def __init__(self, identity: SourceIdentity) -> None:
        self.identity = identity
        self.columns = ("Variant_ID", "AL_1", "note")
        self.column_types = ("text", "number", "text")
        self.closed = False

    def row_at(self, source_row_index: int) -> tuple[str, ...]:
        assert source_row_index == 1
        return ("VAR-002", "0.8", "selected original row")

    def close(self) -> None:
        self.closed = True


class MemoryReader:
    def __init__(self, source: MemorySource) -> None:
        self.source = source
        self.opened_paths: list[Path] = []

    def open(self, path: Path) -> MemorySource:
        self.opened_paths.append(path)
        return self.source


def test_source_row_evidence_reads_exact_row_only_after_integrity_validation(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text("Variant_ID,AL_1,note\nVAR-001,0.2,first\nVAR-002,0.8,selected original row\n")
    checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    run = loaded_run(source_path, checksum)
    source = MemorySource(
        SourceIdentity(
            path=source_path,
            file_name=source_path.name,
            row_count=2,
            column_count=3,
            sha256=checksum,
            delimiter="Comma (,)" ,
            encoding="UTF-8",
            last_modified="2026-08-30T12:00:00+03:00",
        )
    )
    reader = MemoryReader(source)
    archive = MemoryArchive(SourceReferenceStatus(SourceReferenceState.AVAILABLE, checksum, checksum))

    evidence = SourceRowEvidenceService(archive, reader).read(run, source_row=2)

    assert evidence.source_row == 2
    assert evidence.state is SourceReferenceState.AVAILABLE
    assert evidence.expected_sha256 == checksum
    assert evidence.current_sha256 == checksum
    assert [(field.name, field.value, field.value_type) for field in evidence.fields] == [
        ("Variant_ID", "VAR-002", "text"),
        ("AL_1", "0.8", "number"),
        ("note", "selected original row", "text"),
    ]
    assert reader.opened_paths == [source_path]


def test_source_row_evidence_never_opens_a_modified_source(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text("Variant_ID,AL_1,note\nVAR-001,0.2,first\nVAR-002,changed,second\n")
    expected = "a" * 64
    current = hashlib.sha256(source_path.read_bytes()).hexdigest()
    run = loaded_run(source_path, expected)
    source = MemorySource(
        SourceIdentity(
            path=source_path,
            file_name=source_path.name,
            row_count=2,
            column_count=3,
            sha256=current,
            delimiter="Comma (,)",
            encoding="UTF-8",
            last_modified="2026-08-30T12:00:00+03:00",
        )
    )
    reader = MemoryReader(source)
    archive = MemoryArchive(
        SourceReferenceStatus(SourceReferenceState.MODIFIED, expected, current)
    )

    evidence = SourceRowEvidenceService(archive, reader).read(run, source_row=2)

    assert evidence.state is SourceReferenceState.MODIFIED
    assert not evidence.is_available
    assert evidence.fields == ()
    assert evidence.expected_sha256 == expected
    assert evidence.current_sha256 == current
    assert "No source values were read" in evidence.detail
    assert reader.opened_paths == []


def test_source_row_evidence_reports_a_missing_source_without_reading_values(tmp_path):
    source_path = tmp_path / "missing-source.csv"
    expected = "c" * 64
    run = loaded_run(source_path, expected)
    source = MemorySource(
        SourceIdentity(
            path=source_path,
            file_name=source_path.name,
            row_count=2,
            column_count=3,
            sha256=expected,
            delimiter="Comma (,)",
            encoding="UTF-8",
            last_modified="2026-08-30T12:00:00+03:00",
        )
    )
    reader = MemoryReader(source)
    archive = MemoryArchive(
        SourceReferenceStatus(SourceReferenceState.MISSING, expected)
    )

    evidence = SourceRowEvidenceService(archive, reader).read(run, source_row=1)

    assert evidence.state is SourceReferenceState.MISSING
    assert evidence.fields == ()
    assert evidence.current_sha256 == ""
    assert "No source values were read" in evidence.detail
    assert reader.opened_paths == []


def test_source_row_evidence_invalidates_cached_values_when_source_changes(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text("Variant_ID,AL_1,note\nVAR-001,0.2,first\nVAR-002,0.8,second\n")
    checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    run = loaded_run(source_path, checksum)
    source = MemorySource(
        SourceIdentity(
            path=source_path,
            file_name=source_path.name,
            row_count=2,
            column_count=3,
            sha256=checksum,
            delimiter="Comma (,)",
            encoding="UTF-8",
            last_modified="2026-08-30T12:00:00+03:00",
        )
    )
    reader = MemoryReader(source)
    archive = MemoryArchive(
        SourceReferenceStatus(SourceReferenceState.AVAILABLE, checksum, checksum)
    )
    service = SourceRowEvidenceService(archive, reader)

    assert service.read(run, source_row=2).is_available
    assert service.read(run, source_row=2).is_available
    assert archive.source_status_calls == 1

    source_path.write_text(
        "Variant_ID,AL_1,note\nVAR-001,0.2,first\nVAR-002,changed,second\n"
    )
    current = "b" * 64
    archive.status = SourceReferenceStatus(SourceReferenceState.MODIFIED, checksum, current)
    evidence = service.read(run, source_row=2)

    assert evidence.state is SourceReferenceState.MODIFIED
    assert evidence.fields == ()
    assert source.closed


def test_source_row_evidence_integrates_with_disk_backed_csv_reader(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text(
        "Variant_ID,AL_1,note\nVAR-001,0.2,first\nVAR-002,,complete original row\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    run = loaded_run(source_path, checksum)
    archive = MemoryArchive(
        SourceReferenceStatus(SourceReferenceState.AVAILABLE, checksum, checksum)
    )
    service = SourceRowEvidenceService(archive, CsvSourceReader())

    evidence = service.read(run, source_row=2)

    assert evidence.is_available
    assert [(field.name, field.value) for field in evidence.fields] == [
        ("Variant_ID", "VAR-002"),
        ("AL_1", ""),
        ("note", "complete original row"),
    ]
    service.close()
