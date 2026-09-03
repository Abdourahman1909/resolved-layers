#!/usr/bin/env bash
# Build the distributable Resolved Layers wheel for Linux.
#
# The wheel carries the application, its QML surfaces, and the shipped
# Computational Health Lab identity assets. It deliberately carries no Model
# Package, no trained weights, and no organizer data. See packaging/README.md.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$PROJECT_ROOT/.venv/bin/python}"
DIST_DIR="${DIST_DIR:-$PROJECT_ROOT/dist}"

if [ ! -x "$PYTHON" ]; then
  echo "Python interpreter not found: $PYTHON" >&2
  echo "Set PYTHON=/path/to/python or create the project .venv first." >&2
  exit 1
fi

echo "==> Regenerating identity assets from the locked reference"
if "$PYTHON" -c "import PIL" 2>/dev/null; then
  "$PYTHON" "$PROJECT_ROOT/scripts/extract_identity_assets.py"
else
  echo "    Pillow is absent; keeping the committed assets unchanged."
  echo "    Install with: $PYTHON -m pip install '.[assets]'"
fi

echo "==> Verifying the shipped assets are present"
"$PYTHON" - <<'PY'
import sys
sys.path.insert(0, "src")
from variant_inference import assets

missing = [p for p in (assets.SYMBOL, assets.LOCKUP) if not p.is_file()]
icons = assets.window_icon_paths()
if missing or not icons:
    print(f"Missing identity assets: {missing or 'icons'}", file=sys.stderr)
    raise SystemExit(1)
print(f"    lockup, symbol, and {len(icons)} icon sizes present")
PY

echo "==> Building the wheel"
rm -rf "$DIST_DIR"
"$PYTHON" -m pip install --quiet --upgrade build
"$PYTHON" -m build --wheel --outdir "$DIST_DIR"

WHEEL="$(ls "$DIST_DIR"/*.whl | head -1)"
echo
echo "Built: $WHEEL"
echo "Install it with: packaging/install-linux.sh \"$WHEEL\""
