from __future__ import annotations

import os
import subprocess
import sys
import hashlib

from variant_inference.application.verified_run import canonical_prediction_payload
from variant_inference.domain.models import (
    PredictionRecord,
    SourceIdentity,
    TransformationAudit,
    VerifiedRun,
)
from variant_inference.infrastructure.run_archive import DirectoryRunArchive


def test_dataset_profile_qml_starts_without_runtime_errors(fixture_dir):
    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "variant_inference",
            "--model-package",
            str(fixture_dir / "development-package" / "manifest.json"),
            "--open",
            str(fixture_dir / "dataset_profile.csv"),
            "--surface",
            "profile",
            "--smoke",
        ),
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "QQmlApplicationEngine failed" not in result.stderr
    assert "ReferenceError" not in result.stderr
    assert "Unable to assign" not in result.stderr


def test_results_qml_reopens_archived_verified_run(tmp_path):
    source_path = tmp_path / "source.csv"
    source_path.write_text(
        "Variant_ID,AL_1,note\nVAR-001,0.58,near threshold\nVAR-002,0.84,selected row\n",
        encoding="utf-8",
    )
    source_checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    predictions = (
        PredictionRecord(1, 0.58, "Benign", {"catboost": 0.52, "lightgbm": 0.64}, 0.06),
        PredictionRecord(2, 0.84, "Pathogenic", {"catboost": 0.82, "lightgbm": 0.86}, 0.02),
    )
    payload = canonical_prediction_payload(predictions)
    run = VerifiedRun(
        run_id="qml-results",
        created_at="2026-08-29T12:00:00+00:00",
        completed_at="2026-08-29T12:00:01+00:00",
        duration_ms=1000,
        source=SourceIdentity(
            path=source_path,
            file_name="source.csv",
            row_count=2,
            column_count=3,
            sha256=source_checksum,
            delimiter="Comma (,)",
            encoding="UTF-8",
            last_modified="2026-08-29T12:00:00+00:00",
        ),
        model_package_id="package",
        model_package_name="CHL Ensemble",
        model_package_version="2026.1",
        model_package_manifest_checksum="1" * 64,
        inference_contract_id="contract",
        inference_contract_version="2026.1",
        inference_contract_checksum="2" * 64,
        release_threshold=0.61,
        predictions=predictions,
        predictions_sha256=hashlib.sha256(payload).hexdigest(),
        warnings=(),
        transformation_audit=TransformationAudit(),
    )
    archive = DirectoryRunArchive(tmp_path / "archive")
    archive.save(run)
    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"

    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "variant_inference",
            "--run-archive",
            str(archive.root),
            "--open-run",
            run.run_id,
            "--inspect-source-row",
            "2",
            "--smoke",
        ),
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "QQmlApplicationEngine failed" not in result.stderr
    assert "ReferenceError" not in result.stderr
    assert "Unable to assign" not in result.stderr


def _evaluation_archive(tmp_path, labels=("case", "case", "control", "control")):
    source_path = tmp_path / "evaluation-source.csv"
    source_path.write_text(
        "Variant_ID,GroundTruth,_panel\n"
        + "\n".join(
            f"VAR-{index:03d},{label},PANEL-{1 if index <= 2 else 2}"
            for index, label in enumerate(labels, 1)
        )
        + "\n",
        encoding="utf-8",
    )
    source_checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
    predictions = (
        PredictionRecord(1, 0.90, "Pathogenic", {"catboost": 0.92, "lightgbm": 0.88}, 0.02),
        PredictionRecord(2, 0.20, "Benign", {"catboost": 0.18, "lightgbm": 0.22}, 0.02),
        PredictionRecord(3, 0.80, "Pathogenic", {"catboost": 0.82, "lightgbm": 0.78}, 0.02),
        PredictionRecord(4, 0.10, "Benign", {"catboost": 0.08, "lightgbm": 0.12}, 0.02),
    )
    payload = canonical_prediction_payload(predictions)
    run = VerifiedRun(
        run_id="qml-evaluation",
        created_at="2026-08-30T12:00:00+00:00",
        completed_at="2026-08-30T12:00:01+00:00",
        duration_ms=1000,
        source=SourceIdentity(
            path=source_path,
            file_name=source_path.name,
            row_count=4,
            column_count=3,
            sha256=source_checksum,
            delimiter="Comma (,)",
            encoding="UTF-8",
            last_modified="2026-08-30T12:00:00+00:00",
        ),
        model_package_id="package",
        model_package_name="CHL Ensemble",
        model_package_version="2026.1",
        model_package_manifest_checksum="1" * 64,
        inference_contract_id="contract",
        inference_contract_version="2026.1",
        inference_contract_checksum="2" * 64,
        release_threshold=0.61,
        predictions=predictions,
        predictions_sha256=hashlib.sha256(payload).hexdigest(),
        warnings=(),
        transformation_audit=TransformationAudit(),
    )
    archive = DirectoryRunArchive(tmp_path / "evaluation-archive")
    archive.save(run)
    return archive, run, source_path


def _run_evaluation_smoke(archive, run, *extra):
    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "variant_inference",
            "--run-archive",
            str(archive.root),
            "--open-run",
            run.run_id,
            "--surface",
            "evaluation",
            *extra,
            "--smoke",
        ),
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "QQmlApplicationEngine failed" not in result.stderr
    assert "ReferenceError" not in result.stderr
    assert "Unable to assign" not in result.stderr


def test_evaluation_qml_smoke_paths_cover_authorized_unlabeled_missing_and_modified(tmp_path):
    archive, run, source_path = _evaluation_archive(tmp_path)
    _run_evaluation_smoke(
        archive,
        run,
        "--evaluation-label-column",
        "GroundTruth",
        "--evaluation-pathogenic-value",
        "case",
        "--evaluation-benign-value",
        "control",
    )
    _run_evaluation_smoke(archive, run)

    source_path.write_text(source_path.read_text(encoding="utf-8") + "modified", encoding="utf-8")
    _run_evaluation_smoke(archive, run)

    source_path.unlink()
    _run_evaluation_smoke(archive, run)


def test_evaluation_qml_renders_the_group_breakdown(tmp_path):
    archive, run, _ = _evaluation_archive(tmp_path)
    _run_evaluation_smoke(
        archive,
        run,
        "--evaluation-label-column",
        "GroundTruth",
        "--evaluation-pathogenic-value",
        "case",
        "--evaluation-benign-value",
        "control",
        "--evaluation-group-column",
        "_panel",
    )


def _run_settings_smoke(tmp_path, *arguments: str) -> None:
    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["XDG_CONFIG_HOME"] = str(tmp_path / "config")
    # Settings must stand on its own, so neither inherited variable may leak in.
    environment.pop("CHL_MODEL_PACKAGE_MANIFEST", None)
    environment.pop("CHL_TRUSTED_MODEL_PACKAGE_SHA256", None)

    result = subprocess.run(
        (sys.executable, "-m", "variant_inference", "--surface", "settings", "--smoke", *arguments),
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "QQmlApplicationEngine failed" not in result.stderr
    assert "ReferenceError" not in result.stderr
    assert "Unable to assign" not in result.stderr


def test_settings_qml_starts_without_a_model_package(tmp_path):
    _run_settings_smoke(tmp_path)


def test_settings_qml_starts_with_an_installed_model_package(tmp_path, fixture_dir):
    from variant_inference.application.model_package_settings import (
        ModelPackageInstallationService,
    )
    from variant_inference.infrastructure.model_package import JsonModelPackageRepository
    from variant_inference.infrastructure.model_package_store import (
        JsonModelPackageSettingsStore,
    )

    config = tmp_path / "config" / "Computational Health Lab" / "Resolved Layers"
    store = JsonModelPackageSettingsStore(config / "model-package.json")
    service = ModelPackageInstallationService(JsonModelPackageRepository(), store)
    service.install(service.confirm(service.inspect(fixture_dir / "development-package")))

    _run_settings_smoke(tmp_path)


def test_settings_qml_renders_the_override_band(tmp_path, fixture_dir):
    """An argument naming a different package must render the warning band.

    The band is only created when an override is active, so the surface's other
    smoke paths never instantiate it.
    """
    from variant_inference.application.model_package_settings import (
        ModelPackageInstallationService,
    )
    from variant_inference.infrastructure.model_package import JsonModelPackageRepository
    from variant_inference.infrastructure.model_package_store import (
        JsonModelPackageSettingsStore,
    )

    config = tmp_path / "config" / "Computational Health Lab" / "Resolved Layers"
    store = JsonModelPackageSettingsStore(config / "model-package.json")
    service = ModelPackageInstallationService(JsonModelPackageRepository(), store)
    service.install(service.confirm(service.inspect(fixture_dir / "development-package")))

    # A path that is not the installed package, so the two genuinely disagree.
    _run_settings_smoke(
        tmp_path, "--model-package", str(tmp_path / "elsewhere" / "manifest.json")
    )


def test_settings_qml_starts_when_the_installed_package_has_vanished(tmp_path):
    from variant_inference.domain.models import ModelPackageSettings
    from variant_inference.infrastructure.model_package_store import (
        JsonModelPackageSettingsStore,
    )

    config = tmp_path / "config" / "Computational Health Lab" / "Resolved Layers"
    store = JsonModelPackageSettingsStore(config / "model-package.json")
    store.save(ModelPackageSettings(manifest_path=tmp_path / "gone" / "manifest.json"))

    # Fail closed and still render, rather than refusing to start.
    _run_settings_smoke(tmp_path)


def test_submission_qml_starts_for_a_completed_run(tmp_path):
    archive, run, _ = _evaluation_archive(tmp_path)
    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        (
            sys.executable, "-m", "variant_inference",
            "--run-archive", str(archive),
            "--open-run", run.run_id,
            "--surface", "submission",
            "--smoke",
        ),
        check=False, capture_output=True, env=environment, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "QQmlApplicationEngine failed" not in result.stderr
    assert "ReferenceError" not in result.stderr
    assert "Unable to assign" not in result.stderr
