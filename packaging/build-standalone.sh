#!/usr/bin/env bash
# Build the standalone Resolved Layers application for Linux.
#
# Produces a self-contained build that runs without Python installed, and
# optionally an AppImage: one file the recipient makes executable and opens.
#
# The build carries no Model Package, no trained weights, and no organizer data.
# A package is supplied separately and installed from Settings.
#
# The build must not run from a directory whose path contains spaces:
# PyInstaller splits such paths when resolving shared-library dependencies. This
# script therefore stages a copy in a space-free working directory, which also
# keeps the build independent of the development checkout.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${WORK_ROOT:-${TMPDIR:-/tmp}/resolved-layers-build}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_ROOT/dist}"
APP_ID="org.computationalhealthlab.ResolvedLayers"
APPIMAGE_TOOL="${APPIMAGE_TOOL:-}"
BUILD_APPIMAGE="${BUILD_APPIMAGE:-1}"

case "$PROJECT_ROOT" in
  *\ *) echo "==> Project path contains spaces; staging a space-free copy" ;;
esac

echo "==> Staging the source at $WORK_ROOT"
rm -rf "$WORK_ROOT"
mkdir -p "$WORK_ROOT"
tar -c \
  --exclude=.venv --exclude=.git --exclude=dist --exclude=build \
  --exclude=__pycache__ --exclude='*.egg-info' \
  -C "$PROJECT_ROOT" . | tar -x -C "$WORK_ROOT"

echo "==> Creating an isolated build environment"
python3 -m venv "$WORK_ROOT/venv"
"$WORK_ROOT/venv/bin/python" -m pip install --quiet --upgrade pip
"$WORK_ROOT/venv/bin/python" -m pip install --quiet "$WORK_ROOT" pyinstaller pillow

echo "==> Regenerating identity assets from the locked reference"
"$WORK_ROOT/venv/bin/python" "$WORK_ROOT/scripts/extract_identity_assets.py"

echo "==> Building the standalone application"
(
  cd "$WORK_ROOT"
  ./venv/bin/pyinstaller packaging/resolved-layers.spec \
    --distpath "$WORK_ROOT/dist" \
    --workpath "$WORK_ROOT/work" \
    --noconfirm \
    --log-level WARN
)

BUILD_DIR="$WORK_ROOT/dist/resolved-layers"
if [ ! -x "$BUILD_DIR/resolved-layers" ]; then
  echo "The standalone executable was not produced." >&2
  exit 1
fi

echo "==> Verifying the build starts without a Model Package"
(
  cd /
  env -u PYTHONPATH -u VIRTUAL_ENV \
      -u CHL_MODEL_PACKAGE_MANIFEST -u CHL_TRUSTED_MODEL_PACKAGE_SHA256 \
      QT_QPA_PLATFORM=offscreen \
      XDG_CONFIG_HOME="$WORK_ROOT/verify-config" \
      "$BUILD_DIR/resolved-layers" --smoke
)
echo "    starts cleanly"

mkdir -p "$OUTPUT_DIR"

if [ "$BUILD_APPIMAGE" != "1" ]; then
  echo "==> Packing a tarball"
  tar -czf "$OUTPUT_DIR/resolved-layers-linux-x86_64.tar.gz" -C "$WORK_ROOT/dist" resolved-layers
  echo "Built: $OUTPUT_DIR/resolved-layers-linux-x86_64.tar.gz"
  exit 0
fi

echo "==> Assembling the AppDir"
APPDIR="$WORK_ROOT/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications"
cp -a "$BUILD_DIR/." "$APPDIR/usr/bin/"

ICONS="$WORK_ROOT/src/variant_inference/assets/icons"
for size in 16 24 32 48 64 128 256 512; do
  icon="$ICONS/resolved-layers-$size.png"
  [ -f "$icon" ] || continue
  target="$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps"
  mkdir -p "$target"
  cp "$icon" "$target/$APP_ID.png"
done
# appimagetool requires the icon and desktop entry at the AppDir root.
cp "$ICONS/resolved-layers-256.png" "$APPDIR/$APP_ID.png"

# The AppImage runs the binary directly rather than a launcher on PATH.
sed 's|^Exec=resolved-layers|Exec=resolved-layers|' \
  "$WORK_ROOT/packaging/$APP_ID.desktop" > "$APPDIR/$APP_ID.desktop"
cp "$APPDIR/$APP_ID.desktop" "$APPDIR/usr/share/applications/$APP_ID.desktop"

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
# Resolved Layers AppImage entry point.
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/resolved-layers" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

if [ -z "$APPIMAGE_TOOL" ]; then
  if command -v appimagetool >/dev/null 2>&1; then
    APPIMAGE_TOOL="appimagetool"
  else
    echo "appimagetool was not found." >&2
    echo "Set APPIMAGE_TOOL=/path/to/appimagetool, or rerun with BUILD_APPIMAGE=0" >&2
    echo "to produce a tarball instead." >&2
    exit 1
  fi
fi

echo "==> Building the AppImage"
APPIMAGE="$OUTPUT_DIR/Resolved_Layers-x86_64.AppImage"
rm -f "$APPIMAGE"
ARCH=x86_64 "$APPIMAGE_TOOL" --no-appstream "$APPDIR" "$APPIMAGE"

echo
echo "Built: $APPIMAGE"
echo "Run it with: chmod +x \"$APPIMAGE\" && \"$APPIMAGE\""
echo
echo "No Model Package is included. Install one from Settings inside the application."
