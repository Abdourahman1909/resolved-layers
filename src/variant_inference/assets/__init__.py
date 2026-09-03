"""Shipped Computational Health Lab identity assets.

These files are cut from the locked identity reference by
`scripts/extract_identity_assets.py`. They live inside the installed package so
a packaged build resolves them the same way it resolves `qml/`, without
depending on a development checkout or a design-process directory.
"""

from __future__ import annotations

from pathlib import Path

ASSETS_ROOT = Path(__file__).resolve().parent

SYMBOL = ASSETS_ROOT / "identity" / "resolved-layers-symbol.png"
LOCKUP = ASSETS_ROOT / "identity" / "resolved-layers-lockup.png"
# Paired with live wordmark text in the application bar.
SYMBOL_BAR = ASSETS_ROOT / "identity" / "resolved-layers-symbol-bar.png"

WINDOW_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def icon(size: int) -> Path:
    """Return the square application icon rendered at `size` pixels."""
    return ASSETS_ROOT / "icons" / f"resolved-layers-{size}.png"


def window_icon_paths() -> list[Path]:
    """Return every present application icon size, smallest first."""
    return [path for path in (icon(size) for size in WINDOW_ICON_SIZES) if path.is_file()]
