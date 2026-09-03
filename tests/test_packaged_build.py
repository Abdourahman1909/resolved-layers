"""A packaged build ships identity assets and degrades honestly without a model.

The distributed Linux build carries no Model Package. Source Review, Dataset
Profile, and archived Verified Runs must stay usable, prediction must state the
real reason it is unavailable, and the shipped Computational Health Lab identity
must resolve from inside the installed package rather than a development
checkout or a design-process directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from variant_inference import assets
from variant_inference.qt.controller import SourceReviewController
from variant_inference.qt.profile_model import GroupBreakdownModel
from variant_inference.qt.table_model import CsvTableModel

FIXTURE = Path(__file__).parent / "fixtures" / "dataset_profile.csv"


def controller_without_package() -> SourceReviewController:
    return SourceReviewController(
        CsvTableModel(),
        GroupBreakdownModel(),
        package=None,
        identity_lockup=assets.LOCKUP if assets.LOCKUP.is_file() else None,
        verified_runs=None,
        run_unavailable_reason="No Model Package installed",
    )


def test_shipped_identity_assets_live_inside_the_package() -> None:
    assert assets.ASSETS_ROOT.is_dir()
    assert assets.SYMBOL.is_file()
    assert assets.LOCKUP.is_file()

    package_root = Path(assets.__file__).resolve().parents[1]
    assert assets.ASSETS_ROOT.is_relative_to(package_root)


def test_every_declared_window_icon_size_ships() -> None:
    icons = assets.window_icon_paths()
    assert len(icons) == len(assets.WINDOW_ICON_SIZES)
    assert all(path.is_file() for path in icons)


def test_no_shipped_asset_points_into_the_design_process_directory() -> None:
    for path in [assets.SYMBOL, assets.LOCKUP, *assets.window_icon_paths()]:
        assert ".impeccable" not in path.parts


def test_package_less_build_names_the_missing_model_package() -> None:
    controller = controller_without_package()
    controller.openSource(FIXTURE.as_uri())

    assert controller.hasSource is True
    assert controller.runEnabled is False
    assert controller.runButtonText == "No Model Package installed"


def test_package_less_build_does_not_blame_the_reviewed_source() -> None:
    controller = controller_without_package()
    controller.openSource(FIXTURE.as_uri())

    # The reviewed CSV has no defect; only the Model Package is absent.
    assert controller.runButtonText != "Resolve blocking issues"


def test_package_less_build_still_exposes_the_identity_lockup() -> None:
    controller = controller_without_package()
    assert controller.identityLockupUrl != ""
    assert controller.identityLockupUrl.endswith("resolved-layers-lockup.png")


@pytest.mark.parametrize("size", assets.WINDOW_ICON_SIZES)
def test_icons_are_square_and_transparent(size: int) -> None:
    png = assets.icon(size).read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"

    width = int.from_bytes(png[16:20], "big")
    height = int.from_bytes(png[20:24], "big")
    colour_type = png[25]

    assert (width, height) == (size, size)
    assert colour_type == 6, "icons must keep an alpha channel"
