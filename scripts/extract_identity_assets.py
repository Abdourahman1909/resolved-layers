"""Extract shipped identity assets from the locked Resolved Layers reference.

This script does not design, redraw, or reinterpret the Computational Health Lab
identity. It cuts the already-approved symbol and horizontal lockup out of the
locked raster reference sheet, removes the sheet background, and writes the
transparent assets and application icons the packaged desktop build needs.

The approved reference is `.impeccable/mocks/identity/resolved-layers.png`
(brand identity system, version 1.0). Regenerate with:

    .venv/bin/python scripts/extract_identity_assets.py

Regenerating must reproduce byte-identical output from an unchanged reference.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE = PROJECT_ROOT / ".impeccable" / "mocks" / "identity" / "resolved-layers.png"
PACKAGE_ASSETS = PROJECT_ROOT / "src" / "variant_inference" / "assets"
IDENTITY_DIR = PACKAGE_ASSETS / "identity"
ICON_DIR = PACKAGE_ASSETS / "icons"

# Search windows inside the reference sheet. Each window excludes the panel
# caption above it and the panel rule beside it, so the measured bounding box is
# the artwork itself rather than surrounding sheet furniture.
SYMBOL_WINDOW = (70, 165, 545, 645)  # panel 01, SYMBOL
LOCKUP_WINDOW = (615, 170, 1470, 345)  # panel 02, HORIZONTAL LOCKUP

BACKGROUND = np.array([250, 249, 247], dtype=float)
ALPHA_FLOOR = 12  # summed per-channel distance treated as pure background

ICON_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
ICON_PADDING = 0.10  # fraction of the canvas left clear on the tightest axis


def _content_bounds(mask: np.ndarray, window: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    left, top, right, bottom = window
    region = mask[top:bottom, left:right]
    rows, columns = np.nonzero(region)
    if rows.size == 0:
        raise SystemExit(f"No artwork found in reference window {window}.")
    return (
        left + int(columns.min()),
        top + int(rows.min()),
        left + int(columns.max()) + 1,
        top + int(rows.max()) + 1,
    )


def _unmatted(reference: np.ndarray, bounds: tuple[int, int, int, int]) -> Image.Image:
    """Lift artwork off the sheet background, preserving antialiased edges.

    The reference draws dark strokes over a known flat background. For each
    pixel the strongest per-channel darkening gives the coverage, and dividing
    the remaining colour by that coverage recovers the unmatted stroke colour.
    """
    left, top, right, bottom = bounds
    patch = reference[top:bottom, left:right].astype(float)

    coverage = np.max((BACKGROUND - patch) / BACKGROUND, axis=2)
    alpha = np.clip(coverage, 0.0, 1.0)

    safe = np.maximum(alpha, 1e-6)[..., None]
    colour = (patch - BACKGROUND * (1.0 - safe)) / safe
    colour = np.clip(colour, 0.0, 255.0)

    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[..., :3] = np.rint(colour).astype(np.uint8)
    rgba[..., 3] = np.rint(alpha * 255.0).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def _square_icon(symbol: Image.Image, size: int) -> Image.Image:
    """Centre the symbol on a transparent square canvas with even breathing room."""
    usable = max(1, int(round(size * (1.0 - 2.0 * ICON_PADDING))))
    scale = min(usable / symbol.width, usable / symbol.height)
    width = max(1, int(round(symbol.width * scale)))
    height = max(1, int(round(symbol.height * scale)))

    resized = symbol.resize((width, height), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - width) // 2, (size - height) // 2), resized)
    return canvas


def main() -> int:
    if not REFERENCE.is_file():
        raise SystemExit(f"Locked identity reference is missing: {REFERENCE}")

    reference = np.asarray(Image.open(REFERENCE).convert("RGB"))
    mask = np.abs(reference.astype(int) - BACKGROUND.astype(int)).sum(axis=2) > ALPHA_FLOOR

    symbol = _unmatted(reference, _content_bounds(mask, SYMBOL_WINDOW))
    lockup = _unmatted(reference, _content_bounds(mask, LOCKUP_WINDOW))

    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    symbol.save(IDENTITY_DIR / "resolved-layers-symbol.png", optimize=True)
    lockup.save(IDENTITY_DIR / "resolved-layers-lockup.png", optimize=True)

    icons = [(size, _square_icon(symbol, size)) for size in ICON_SIZES]
    for size, icon in icons:
        icon.save(ICON_DIR / f"resolved-layers-{size}.png", optimize=True)

    largest = dict(icons)[max(ICO_SIZES)]
    largest.save(ICON_DIR / "resolved-layers.ico", sizes=[(s, s) for s in ICO_SIZES])

    print(f"symbol  {symbol.width}x{symbol.height}")
    print(f"lockup  {lockup.width}x{lockup.height}")
    print(f"icons   {', '.join(str(size) for size in ICON_SIZES)} and .ico")
    return 0


if __name__ == "__main__":
    sys.exit(main())
