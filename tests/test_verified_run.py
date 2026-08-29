from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest

from variant_inference.application.verified_run import VerifiedRunError, VerifiedRunService
from variant_inference.domain.models import (
    AuditEntry,
    ContractFit,
    Finding,
    PredictionRecord,
    SourceIdentity,
    SourceReferenceState,
    TransformationAudit,
)
from variant_inference.infrastructure.run_archive import DirectoryRunArchive


class FixedInference:
    def predict(self, source, package):
        return tuple(
            PredictionRecord(
                source_row=index + 1,
                ensemble_score=score,
                prediction="Pathogenic" if score >= package.contract.release_threshold else "Benign",
                component_scores={"catboost": score, "lightgbm": score},
                model_disagreement=0.0,
            )
            for index, score in enumerate((0.2, 0.8))
        )


def compatible_fit() -> ContractFit:
    return ContractFit(
        required_count=2,
        available_required_count=2,
        missing_required=(),
        missing_omissible=("omissible_panel",),
        surplus_columns=("label",),
        warnings=(
            Finding(
                "missing_omissible",
                "One Omissible Model Feature uses its declared missing representation.",
                ("omissible_panel",),
            ),
        ),
    )


def test_verified_run_is_atomic_traceable_and_does_not_copy_source(
    tmp_path, model_package
):
    source_path = tmp_path / "source.csv"
    source_path.write_text("required_numeric,required_category\n0.2,A\n0.8,B\n", encoding="utf-8")
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()

    from conftest import MemorySource

    source = MemorySource(("required_numeric", "required_category"))
    source.identity = SourceIdentity(
        path=source_path,
        file_name=source_path.name,
        row_count=2,
        column_count=2,
        sha256=source_hash,
        delimiter="Comma (,)",
        encoding="UTF-8",
        last_modified="2026-08-29T12:00:00+03:00",
    )
    archive = DirectoryRunArchive(tmp_path / "archive")
    times = iter(
        (
            datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 29, 12, 0, 1, tzinfo=timezone.utc),
        )
    )
    timer = iter((10.0, 10.125))
    service = VerifiedRunService(
        FixedInference(),
        archive,
        clock=lambda: next(times),
        timer=lambda: next(timer),
        run_id_factory=lambda _: "run-fixed",
    )
    audit = TransformationAudit(
        (AuditEntry("row_filtering", "None", "Every Source Row is preserved."),)
    )

    archived = service.execute(
        source=source,
        package=model_package,
        fit=compatible_fit(),
        audit=audit,
        operator_confirmed=True,
    )

    assert archived.run_id == "run-fixed"
    assert {path.name for path in archived.directory.iterdir()} == {
        "manifest.json",
        "predictions.jsonl",
    }
    manifest = json.loads(archived.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "verified"
    assert manifest["duration_ms"] == 125
    assert manifest["source"]["sha256"] == source_hash
    assert manifest["source"]["snapshot"] == {"included": False}
    assert manifest["model_package"]["manifest_sha256"] == model_package.manifest_checksum
    assert manifest["inference_contract"]["release_threshold"] == 0.61
    assert manifest["output"]["record_count"] == 2
    assert manifest["output"]["pathogenic_count"] == 1
    assert manifest["output"]["benign_count"] == 1
    assert manifest["output"]["sha256"] == hashlib.sha256(
        archived.predictions_path.read_bytes()
    ).hexdigest()
    assert manifest["warnings"][0]["code"] == "missing_omissible"
    assert manifest["transformation_audit"][0]["topic"] == "row_filtering"

    repeated_times = iter(
        (
            datetime(2026, 8, 29, 12, 1, tzinfo=timezone.utc),
            datetime(2026, 8, 29, 12, 1, 1, tzinfo=timezone.utc),
        )
    )
    repeated_timer = iter((20.0, 20.125))
    repeated_service = VerifiedRunService(
        FixedInference(),
        archive,
        clock=lambda: next(repeated_times),
        timer=lambda: next(repeated_timer),
        run_id_factory=lambda _: "run-fixed",
    )
    with pytest.raises(RuntimeError, match="already exists"):
        repeated_service.execute(
            source=source,
            package=model_package,
            fit=compatible_fit(),
            audit=audit,
            operator_confirmed=True,
        )

    assert archive.source_status("run-fixed").state is SourceReferenceState.AVAILABLE
    source_path.write_text("changed\n", encoding="utf-8")
    assert archive.source_status("run-fixed").state is SourceReferenceState.MODIFIED
    source_path.unlink()
    assert archive.source_status("run-fixed").state is SourceReferenceState.MISSING


def test_verified_run_requires_confirmation_and_exact_source_row_order(
    tmp_path, model_package
):
    from conftest import MemorySource

    source = MemorySource(("required_numeric", "required_category"))
    archive = DirectoryRunArchive(tmp_path / "archive")
    service = VerifiedRunService(FixedInference(), archive)

    with pytest.raises(VerifiedRunError, match="confirmation"):
        service.execute(
            source=source,
            package=model_package,
            fit=compatible_fit(),
            audit=TransformationAudit(),
            operator_confirmed=False,
        )
    assert not archive.root.exists()


def test_archive_rejects_unsafe_run_identifier(tmp_path, model_package):
    from conftest import MemorySource

    source = MemorySource(("required_numeric", "required_category"))
    service = VerifiedRunService(
        FixedInference(),
        DirectoryRunArchive(tmp_path / "archive"),
        run_id_factory=lambda _: "../escape",
    )
    with pytest.raises(RuntimeError, match="identifier"):
        service.execute(
            source=source,
            package=model_package,
            fit=compatible_fit(),
            audit=TransformationAudit(),
            operator_confirmed=True,
        )
