"""Settings must describe the package that is predicting, not just its own file.

An argument and an environment variable both take priority over the package
installed through Settings. That is deliberate, but it used to be invisible: the
surface reported the installed package as ready while a different one did the
predicting.

This matters more now that two packages hold the same weights and differ only in
their Release Threshold. Name, version, and location can all look right while the
classification boundary is the other one, and nothing on screen would say so.

These tests pin the resolution decision and what the surface reports. What a
control does when clicked is not testable here; the limit recorded in
`test_archive_delete_ui.py` applies to this surface too.
"""

from __future__ import annotations

from pathlib import Path

from variant_inference.application.model_package_settings import (
    ModelPackageInstallationService,
)
from variant_inference.infrastructure.model_package import JsonModelPackageRepository
from variant_inference.infrastructure.model_package_store import (
    JsonModelPackageSettingsStore,
)
from variant_inference.main import _same_package
from variant_inference.qt.model_package_controller import ModelPackageController

FIXTURE_PACKAGE = Path(__file__).parent / "fixtures" / "development-package"


def _installed_service(tmp_path: Path) -> ModelPackageInstallationService:
    store = JsonModelPackageSettingsStore(tmp_path / "config" / "model-package.json")
    service = ModelPackageInstallationService(JsonModelPackageRepository(), store)
    service.install(service.confirm(service.inspect(FIXTURE_PACKAGE)))
    return service


# Which package is actually in use ------------------------------------------


def test_a_folder_and_its_manifest_are_the_same_package(tmp_path: Path) -> None:
    # An override naming the folder must not be reported as a contradiction
    # when Settings stored the manifest inside it.
    assert _same_package(FIXTURE_PACKAGE, FIXTURE_PACKAGE / "manifest.json")


def test_two_different_packages_are_not_the_same(tmp_path: Path) -> None:
    other = tmp_path / "elsewhere" / "manifest.json"
    assert not _same_package(FIXTURE_PACKAGE, other)


def test_nothing_installed_is_never_reported_as_a_contradiction() -> None:
    assert not _same_package(FIXTURE_PACKAGE, None)
    assert not _same_package(None, FIXTURE_PACKAGE / "manifest.json")


# What the surface reports ---------------------------------------------------


def test_an_override_is_reported_instead_of_claiming_the_installed_one_is_ready(
    tmp_path: Path,
) -> None:
    controller = ModelPackageController(
        _installed_service(tmp_path),
        active_override="environment",
        active_manifest_path=tmp_path / "other-package" / "manifest.json",
    )
    controller.refresh_installed()

    assert controller.overrideActive
    assert controller.messageKind == "warning"
    # The status line stays short; the band carries the full explanation, so the
    # operator does not read the same sentence twice.
    assert "CHL_MODEL_PACKAGE_MANIFEST" in controller.overrideSummary
    assert controller.message == controller.overrideSummary
    assert controller.message != controller.overrideMessage
    assert "not the one installed here" in controller.overrideMessage
    assert controller.overridePath == str(tmp_path / "other-package")
    controller.shutdown()


def test_without_an_override_the_installed_package_reads_as_ready(tmp_path: Path) -> None:
    controller = ModelPackageController(_installed_service(tmp_path))
    controller.refresh_installed()

    assert not controller.overrideActive
    assert controller.messageKind == "success"
    assert controller.message == "Model Package ready."
    assert controller.overrideSummary == ""
    assert controller.overrideMessage == ""
    assert controller.overridePath == "—"
    controller.shutdown()


def _await_inspection(controller: ModelPackageController) -> None:
    """Wait until the off-thread inspection and its callback have both finished.

    The executor has a single worker and completion callbacks run on it before
    it takes the next item, so a second task cannot start until the first has
    fully reported. Waiting on that is exact, where a sleep would only be likely.
    """
    controller._executor.submit(lambda: None).result(timeout=15)


def test_installing_under_an_override_does_not_promise_it_will_be_used(
    tmp_path: Path,
) -> None:
    service = _installed_service(tmp_path)
    controller = ModelPackageController(
        service,
        active_override="environment",
        active_manifest_path=tmp_path / "other-package" / "manifest.json",
    )
    controller.selectPackage(str(FIXTURE_PACKAGE))
    _await_inspection(controller)
    assert controller.canInstall

    controller.installSelected()

    assert controller.messageKind == "warning"
    assert "Restart" not in controller.message
    controller.shutdown()


def test_installing_without_an_override_says_a_restart_will_use_it(
    tmp_path: Path,
) -> None:
    controller = ModelPackageController(_installed_service(tmp_path))
    controller.selectPackage(str(FIXTURE_PACKAGE))
    _await_inspection(controller)

    controller.installSelected()

    assert controller.messageKind == "success"
    assert "Restart" in controller.message
    controller.shutdown()


def test_an_argument_override_names_the_argument(tmp_path: Path) -> None:
    controller = ModelPackageController(
        _installed_service(tmp_path),
        active_override="argument",
        active_manifest_path=tmp_path / "other" / "manifest.json",
    )
    controller.refresh_installed()

    assert "--model-package" in controller.overrideSummary
    assert "--model-package" in controller.overrideMessage
    controller.shutdown()


# Telling two packages apart -------------------------------------------------


def test_the_installed_package_reports_its_threshold_and_checksum(tmp_path: Path) -> None:
    # The only evidence that distinguishes two packages built from the same
    # weights.
    controller = ModelPackageController(_installed_service(tmp_path))
    controller.refresh_installed()

    assert controller.installedThreshold == "0.610"
    assert len(controller.installedChecksum) == 64
    assert controller.installedChecksum.strip("0123456789abcdef") == ""
    controller.shutdown()


def test_nothing_installed_reports_no_threshold_or_checksum(tmp_path: Path) -> None:
    store = JsonModelPackageSettingsStore(tmp_path / "config" / "model-package.json")
    controller = ModelPackageController(
        ModelPackageInstallationService(JsonModelPackageRepository(), store)
    )
    controller.refresh_installed()

    assert controller.installedThreshold == "—"
    assert controller.installedChecksum == "—"
    controller.shutdown()


def test_an_environment_package_is_disclosed_even_with_nothing_installed(
    tmp_path: Path,
) -> None:
    """Prediction works while Settings has nothing; say where the package came from.

    Reporting only "No Model Package installed" would describe the settings file
    rather than the application, on the machine where the environment variable is
    the only route a package arrives by.
    """
    store = JsonModelPackageSettingsStore(tmp_path / "config" / "model-package.json")
    controller = ModelPackageController(
        ModelPackageInstallationService(JsonModelPackageRepository(), store),
        active_override="environment",
        active_manifest_path=FIXTURE_PACKAGE / "manifest.json",
    )
    controller.refresh_installed()

    assert not controller.hasInstalled
    assert controller.overrideActive
    assert controller.messageKind == "warning"
    assert controller.message != "No Model Package installed."
    assert "CHL_MODEL_PACKAGE_MANIFEST" in controller.overrideMessage
    assert "Nothing is installed here" in controller.overrideMessage
    assert controller.overridePath == str(FIXTURE_PACKAGE)
    controller.shutdown()


def test_the_same_package_by_two_routes_is_not_called_an_override(
    tmp_path: Path,
) -> None:
    # main() clears the override when both routes resolve to one manifest, so
    # pointing the variable at the installed package raises no warning.
    from variant_inference.main import _same_package

    assert _same_package(FIXTURE_PACKAGE, FIXTURE_PACKAGE / "manifest.json")

    controller = ModelPackageController(_installed_service(tmp_path))
    controller.refresh_installed()

    assert not controller.overrideActive
    assert controller.messageKind == "success"
    controller.shutdown()


# Disclosed where the run is confirmed -----------------------------------------


def _review_controller(override: str = ""):
    """A Source Review controller holding the fixture package."""
    from variant_inference.qt.controller import SourceReviewController
    from variant_inference.qt.profile_model import GroupBreakdownModel
    from variant_inference.qt.table_model import CsvTableModel

    package = JsonModelPackageRepository().load(FIXTURE_PACKAGE / "manifest.json")
    return SourceReviewController(
        CsvTableModel(),
        GroupBreakdownModel(),
        package,
        package_override=override,
    )


def test_source_review_shows_the_threshold_the_run_will_use() -> None:
    # The operator confirms a run here. Two packages can differ only in this
    # number, so the package name alone does not identify the run being created.
    controller = _review_controller()

    assert controller.packageThreshold == "0.610"


def test_source_review_discloses_an_override_before_the_run() -> None:
    """The Settings band arrives after the run it should have preceded."""
    controller = _review_controller("environment")

    assert controller.packageOverridden
    assert "CHL_MODEL_PACKAGE_MANIFEST" in controller.packageOverrideNotice
    assert "not from Settings" in controller.packageOverrideNotice


def test_source_review_says_nothing_when_settings_supplied_the_package() -> None:
    controller = _review_controller()

    assert not controller.packageOverridden
    assert controller.packageOverrideNotice == ""


def test_source_review_reports_no_threshold_without_a_package() -> None:
    from variant_inference.qt.controller import SourceReviewController
    from variant_inference.qt.profile_model import GroupBreakdownModel
    from variant_inference.qt.table_model import CsvTableModel

    controller = SourceReviewController(CsvTableModel(), GroupBreakdownModel(), None)

    assert controller.packageThreshold == "—"
