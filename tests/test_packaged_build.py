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
        identity_symbol=assets.SYMBOL_BAR if assets.SYMBOL_BAR.is_file() else None,
        verified_runs=None,
        run_unavailable_reason="No Model Package installed",
    )


def test_shipped_identity_assets_live_inside_the_package() -> None:
    assert assets.ASSETS_ROOT.is_dir()
    assert assets.SYMBOL.is_file()
    assert assets.LOCKUP.is_file()
    assert assets.SYMBOL_BAR.is_file()

    package_root = Path(assets.__file__).resolve().parents[1]
    assert assets.ASSETS_ROOT.is_relative_to(package_root)


def test_every_declared_window_icon_size_ships() -> None:
    icons = assets.window_icon_paths()
    assert len(icons) == len(assets.WINDOW_ICON_SIZES)
    assert all(path.is_file() for path in icons)


def test_no_shipped_asset_points_into_the_design_process_directory() -> None:
    for path in [assets.SYMBOL, assets.LOCKUP, assets.SYMBOL_BAR, *assets.window_icon_paths()]:
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


def test_package_less_build_still_exposes_the_identity_symbol() -> None:
    controller = controller_without_package()
    assert controller.identitySymbolUrl != ""
    assert controller.identitySymbolUrl.endswith("resolved-layers-symbol-bar.png")


@pytest.mark.parametrize("size", assets.WINDOW_ICON_SIZES)
def test_icons_are_square_and_transparent(size: int) -> None:
    png = assets.icon(size).read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"

    width = int.from_bytes(png[16:20], "big")
    height = int.from_bytes(png[20:24], "big")
    colour_type = png[25]

    assert (width, height) == (size, size)
    assert colour_type == 6, "icons must keep an alpha channel"


# Standalone build verification ---------------------------------------------


def test_verify_inference_needs_a_package_and_a_source(capsys) -> None:
    """The packaging self-test refuses to report success on missing inputs."""
    from variant_inference.main import build_parser, verify_inference

    args = build_parser().parse_args(["--verify-inference"])

    assert verify_inference(args) == 2
    assert "--model-package" in capsys.readouterr().err


def test_verify_inference_reports_an_invalid_package(tmp_path, capsys) -> None:
    from variant_inference.main import build_parser, verify_inference

    manifest = tmp_path / "manifest.json"
    manifest.write_text("{ not a manifest", encoding="utf-8")
    source = tmp_path / "source.csv"
    source.write_text("a,b\n1,2\n", encoding="utf-8")

    args = build_parser().parse_args(
        ["--verify-inference", "--model-package", str(manifest), "--open", str(source)]
    )

    assert verify_inference(args) == 3
    assert "rejected" in capsys.readouterr().err


def test_verify_inference_does_not_need_a_display() -> None:
    """It must run before any Qt object exists, so a headless build can self-test."""
    import inspect

    from variant_inference import main as main_module

    body = inspect.getsource(main_module.main)
    verify_call = body.index("verify_inference(args)")
    application_construction = body.index("QGuiApplication(")

    assert verify_call < application_construction


# Version identity -----------------------------------------------------------


def test_the_package_declares_a_single_version() -> None:
    """One source of truth, so a released build cannot misreport itself."""
    import re

    import variant_inference

    assert re.fullmatch(r"\d+\.\d+\.\d+", variant_inference.__version__)

    pyproject = (Path(variant_inference.__file__).parents[2] / "pyproject.toml").read_text()
    assert 'dynamic = ["version"]' in pyproject
    assert 'version = {attr = "variant_inference.__version__"}' in pyproject
    # A literal version in pyproject would be a second, driftable source.
    assert '\nversion = "' not in pyproject


def test_the_version_is_reportable_without_a_display(capsys) -> None:
    """--version must work on a machine with no graphical session."""
    import variant_inference
    from variant_inference.main import build_parser

    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["--version"])

    assert exit_info.value.code == 0
    assert variant_inference.__version__ in capsys.readouterr().out


def test_no_shipped_asset_hides_colour_under_zero_alpha() -> None:
    """Transparent pixels must carry real edge colour, not division artefacts.

    A renderer that scales an image blends colour from fully transparent pixels
    into visible edges. Shipping extreme values there produced visible fringing
    on the identity in the application bar.
    """
    import struct
    import zlib

    for path in (assets.SYMBOL, assets.SYMBOL_BAR, assets.icon(256)):
        image = _decode_rgba(path)
        transparent = [px for px in image if px[3] < 8]
        if not transparent:
            continue
        extremes = sum(
            1
            for r, g, b, _ in transparent
            if (r > 230 and g > 230 and b > 230) or (r + g + b) > 700
        )
        assert extremes / len(transparent) < 0.02, f"{path.name} hides bright colour under alpha 0"


def _decode_rgba(path: Path) -> list[tuple[int, int, int, int]]:
    """Minimal PNG reader, so this assertion needs no imaging dependency."""
    import struct
    import zlib

    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    width = int.from_bytes(raw[16:20], "big")
    height = int.from_bytes(raw[20:24], "big")
    assert raw[25] == 6, "expected 8-bit RGBA"

    idat = b""
    offset = 8
    while offset < len(raw):
        length = int.from_bytes(raw[offset:offset + 4], "big")
        kind = raw[offset + 4:offset + 8]
        if kind == b"IDAT":
            idat += raw[offset + 8:offset + 8 + length]
        offset += 12 + length

    data = zlib.decompress(idat)
    pixels: list[tuple[int, int, int, int]] = []
    stride = width * 4
    previous = bytearray(stride)
    position = 0
    for _ in range(height):
        filter_type = data[position]
        position += 1
        line = bytearray(data[position:position + stride])
        position += stride
        for i in range(stride):
            left = line[i - 4] if i >= 4 else 0
            up = previous[i]
            upper_left = previous[i - 4] if i >= 4 else 0
            if filter_type == 1:
                line[i] = (line[i] + left) & 0xFF
            elif filter_type == 2:
                line[i] = (line[i] + up) & 0xFF
            elif filter_type == 3:
                line[i] = (line[i] + (left + up) // 2) & 0xFF
            elif filter_type == 4:
                p = left + up - upper_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upper_left)
                pred = left if (pa <= pb and pa <= pc) else (up if pb <= pc else upper_left)
                line[i] = (line[i] + pred) & 0xFF
        pixels.extend(
            (line[i], line[i + 1], line[i + 2], line[i + 3]) for i in range(0, stride, 4)
        )
        previous = line
    return pixels
