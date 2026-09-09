"""Installing a Model Package from the interface, without weakening trust.

Model artifacts are unpickled, and unpickling executes code, so structural
validity must never be sufficient on its own. These tests pin the trust rules:
official packages are recognised, anything else requires an explicit operator
confirmation of that exact manifest checksum, and a package that changes after
installation stops being usable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from variant_inference.application.model_package_settings import (
    OFFICIAL_MANIFEST_CHECKSUMS,
    ModelPackageInstallationService,
)
from variant_inference.domain.models import ModelPackageSettings, ModelPackageTrust
from variant_inference.infrastructure.model_package import (
    JsonModelPackageRepository,
    ModelPackageValidationError,
)
from variant_inference.infrastructure.model_package_store import (
    JsonModelPackageSettingsStore,
)

FIXTURE_PACKAGE = Path(__file__).parent / "fixtures" / "development-package"


def service_for(tmp_path: Path, official: frozenset[str] = frozenset()):
    store = JsonModelPackageSettingsStore(tmp_path / "config" / "model-package.json")
    return ModelPackageInstallationService(
        JsonModelPackageRepository(), store, official_checksums=official
    ), store


def checksum_of(manifest: Path) -> str:
    import hashlib

    return hashlib.sha256(manifest.read_bytes()).hexdigest()


# Selection ----------------------------------------------------------------


def test_a_package_folder_is_accepted_not_only_its_manifest(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)

    from_folder = service.inspect(FIXTURE_PACKAGE)
    from_manifest = service.inspect(FIXTURE_PACKAGE / "manifest.json")

    assert from_folder.identity is not None
    assert from_folder.manifest_path == from_manifest.manifest_path


def test_a_folder_without_a_manifest_is_reported_not_raised(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)

    candidate = service.inspect(tmp_path)

    assert candidate.trust is ModelPackageTrust.INVALID
    assert candidate.identity is None
    assert "manifest.json" in candidate.problem


def test_a_tampered_artifact_is_rejected_before_any_model_loads(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    for item in FIXTURE_PACKAGE.iterdir():
        (package / item.name).write_bytes(item.read_bytes())

    manifest = json.loads((package / "manifest.json").read_text())
    artifact = package / manifest["artifacts"][0]["path"]
    artifact.write_bytes(artifact.read_bytes() + b"tampered")

    service, _ = service_for(tmp_path)
    candidate = service.inspect(package)

    assert candidate.trust is ModelPackageTrust.INVALID
    assert candidate.identity is None
    assert "checksum" in candidate.problem.lower()


# Trust --------------------------------------------------------------------


def test_an_unknown_package_is_not_usable_until_confirmed(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)

    candidate = service.inspect(FIXTURE_PACKAGE)

    assert candidate.trust is ModelPackageTrust.UNCONFIRMED
    assert candidate.needs_confirmation is True
    assert candidate.is_usable is False


def test_a_pinned_official_package_needs_no_confirmation(tmp_path: Path) -> None:
    official = frozenset({checksum_of(FIXTURE_PACKAGE / "manifest.json")})
    service, _ = service_for(tmp_path, official=official)

    candidate = service.inspect(FIXTURE_PACKAGE)

    assert candidate.trust is ModelPackageTrust.OFFICIAL
    assert candidate.is_usable is True
    assert candidate.needs_confirmation is False


def test_confirming_records_that_exact_checksum(tmp_path: Path) -> None:
    service, store = service_for(tmp_path)

    confirmed = service.confirm(service.inspect(FIXTURE_PACKAGE))

    assert confirmed.trust is ModelPackageTrust.CONFIRMED
    assert confirmed.is_usable is True
    assert confirmed.manifest_checksum in store.load().confirmed_checksums


def test_confirming_one_package_does_not_trust_another(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)
    service.confirm(service.inspect(FIXTURE_PACKAGE))

    other = tmp_path / "other"
    other.mkdir()
    for item in FIXTURE_PACKAGE.iterdir():
        (other / item.name).write_bytes(item.read_bytes())
    manifest_path = other / "manifest.json"
    payload = json.loads(manifest_path.read_text())
    payload["display_name"] = "A different package"
    manifest_path.write_text(json.dumps(payload))

    candidate = service.inspect(other)

    assert candidate.identity is not None
    assert candidate.trust is ModelPackageTrust.UNCONFIRMED


def test_an_invalid_candidate_cannot_be_confirmed(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)

    with pytest.raises(ValueError):
        service.confirm(service.inspect(tmp_path))


# Installation -------------------------------------------------------------


def test_an_unconfirmed_package_cannot_be_installed(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)

    with pytest.raises(ValueError):
        service.install(service.inspect(FIXTURE_PACKAGE))


def test_installing_survives_a_restart(tmp_path: Path) -> None:
    service, store = service_for(tmp_path)
    service.install(service.confirm(service.inspect(FIXTURE_PACKAGE)))

    restarted = ModelPackageInstallationService(JsonModelPackageRepository(), store)
    configured = restarted.configured()

    assert configured is not None
    assert configured.is_usable is True
    assert configured.identity is not None


def test_trusted_checksums_combine_official_and_confirmed(tmp_path: Path) -> None:
    official = frozenset({"a" * 64})
    service, _ = service_for(tmp_path, official=official)
    confirmed = service.confirm(service.inspect(FIXTURE_PACKAGE))

    trusted = service.trusted_checksums()

    assert "a" * 64 in trusted
    assert confirmed.manifest_checksum in trusted


def test_removing_keeps_the_confirmation_for_next_time(tmp_path: Path) -> None:
    service, store = service_for(tmp_path)
    candidate = service.confirm(service.inspect(FIXTURE_PACKAGE))
    service.install(candidate)

    service.remove()

    assert service.configured() is None
    assert candidate.manifest_checksum in store.load().confirmed_checksums


def test_a_package_that_changes_after_install_stops_being_usable(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    for item in FIXTURE_PACKAGE.iterdir():
        (package / item.name).write_bytes(item.read_bytes())

    service, _ = service_for(tmp_path)
    service.install(service.confirm(service.inspect(package)))

    artifact = package / json.loads((package / "manifest.json").read_text())["artifacts"][0]["path"]
    artifact.write_bytes(artifact.read_bytes() + b"changed")

    configured = service.configured()

    assert configured is not None
    assert configured.is_usable is False
    assert configured.trust is ModelPackageTrust.INVALID


def test_a_missing_package_folder_is_reported_not_crashed(tmp_path: Path) -> None:
    service, _ = service_for(tmp_path)
    service.install(service.confirm(service.inspect(FIXTURE_PACKAGE)))
    service._store.save(  # simulate the package folder disappearing
        ModelPackageSettings(
            manifest_path=tmp_path / "gone" / "manifest.json",
            confirmed_checksums=service.settings().confirmed_checksums,
        )
    )

    configured = service.configured()

    assert configured is not None
    assert configured.is_usable is False


# Store --------------------------------------------------------------------


def test_a_damaged_configuration_never_blocks_startup(tmp_path: Path) -> None:
    path = tmp_path / "model-package.json"
    path.write_text("{ this is not json")
    store = JsonModelPackageSettingsStore(path)

    settings = store.load()

    assert settings.manifest_path is None
    assert settings.confirmed_checksums == frozenset()


def test_an_absent_configuration_reads_as_empty(tmp_path: Path) -> None:
    store = JsonModelPackageSettingsStore(tmp_path / "absent.json")

    assert store.load() == ModelPackageSettings()


def test_a_future_schema_version_is_ignored_rather_than_misread(tmp_path: Path) -> None:
    path = tmp_path / "model-package.json"
    path.write_text(json.dumps({"schema_version": 99, "manifest_path": "/somewhere"}))
    store = JsonModelPackageSettingsStore(path)

    assert store.load().manifest_path is None


def test_the_store_holds_no_model_artifacts(tmp_path: Path) -> None:
    service, store = service_for(tmp_path)
    service.install(service.confirm(service.inspect(FIXTURE_PACKAGE)))

    written = store.path.read_text()

    assert "manifest_path" in written
    for artifact_suffix in (".pkl", ".cbm", ".joblib"):
        assert artifact_suffix not in written


# Pinned official packages ---------------------------------------------------


def test_both_release_thresholds_are_pinned_as_official() -> None:
    """Either package must install on the day without a trust prompt."""
    assert (
        "fc20e611197bbe65f9d5cda058c7367bf32d54df95dd77f5af3d3c59fb8d923d"
        in OFFICIAL_MANIFEST_CHECKSUMS
    ), "the reported 0.61 PDR package"
    assert (
        "b5c8f2e72dfb0b56b73008ee0709cdc46e53fa7299c653ca9ada8a46b82e40f2"
        in OFFICIAL_MANIFEST_CHECKSUMS
    ), "the same release at threshold 0.75"


def test_the_pinned_checksums_are_distinct_and_well_formed() -> None:
    # Changing the threshold changes the Inference Contract and so the manifest
    # checksum; a single shared entry would mean one of them was not pinned.
    assert len(OFFICIAL_MANIFEST_CHECKSUMS) == 2
    for checksum in OFFICIAL_MANIFEST_CHECKSUMS:
        assert len(checksum) == 64
        assert checksum == checksum.lower()
        assert checksum.strip("0123456789abcdef") == ""
