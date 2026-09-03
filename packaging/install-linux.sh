#!/usr/bin/env bash
# Install Resolved Layers for the current user on Linux.
#
# This needs no administrator rights. It creates an isolated runtime under
# ~/.local/opt, exposes the launcher on PATH, and registers the application with
# the desktop environment so it appears in the applications menu with its own
# icon.
#
# No Model Package is installed. Source Review, Dataset Profile, and archived
# Verified Runs work immediately; prediction reports that no Model Package is
# installed until one is supplied separately.

set -euo pipefail

APP_ID="org.computationalhealthlab.ResolvedLayers"
PACKAGING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PREFIX="${PREFIX:-$HOME/.local}"
RUNTIME_DIR="${RUNTIME_DIR:-$PREFIX/opt/resolved-layers}"
BIN_DIR="$PREFIX/bin"
ICON_ROOT="$PREFIX/share/icons/hicolor"
DESKTOP_DIR="$PREFIX/share/applications"

WHEEL="${1:-}"
if [ -z "$WHEEL" ]; then
  WHEEL="$(ls "$PACKAGING_DIR/../dist"/*.whl 2>/dev/null | head -1 || true)"
fi
if [ -z "$WHEEL" ] || [ ! -f "$WHEEL" ]; then
  echo "Usage: $0 /path/to/chl_resolved_layers-*.whl" >&2
  echo "Build one first with packaging/build-linux.sh" >&2
  exit 1
fi

BASE_PYTHON="${BASE_PYTHON:-python3}"
if ! command -v "$BASE_PYTHON" >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH." >&2
  exit 1
fi

echo "==> Creating the isolated runtime at $RUNTIME_DIR"
rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR"
"$BASE_PYTHON" -m venv "$RUNTIME_DIR"

echo "==> Installing the application and its pinned dependencies"
"$RUNTIME_DIR/bin/python" -m pip install --quiet --upgrade pip
"$RUNTIME_DIR/bin/python" -m pip install --quiet "$WHEEL"

echo "==> Exposing the launcher on PATH"
mkdir -p "$BIN_DIR"
ln -sf "$RUNTIME_DIR/bin/resolved-layers" "$BIN_DIR/resolved-layers"

echo "==> Installing application icons"
ICON_SOURCE="$("$RUNTIME_DIR/bin/python" -c 'from variant_inference import assets; print(assets.ASSETS_ROOT)')"
for size in 16 24 32 48 64 128 256 512; do
  icon="$ICON_SOURCE/icons/resolved-layers-$size.png"
  [ -f "$icon" ] || continue
  target="$ICON_ROOT/${size}x${size}/apps"
  mkdir -p "$target"
  cp "$icon" "$target/$APP_ID.png"
done

echo "==> Registering the desktop entry"
mkdir -p "$DESKTOP_DIR"
cp "$PACKAGING_DIR/$APP_ID.desktop" "$DESKTOP_DIR/$APP_ID.desktop"
chmod 644 "$DESKTOP_DIR/$APP_ID.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$ICON_ROOT" >/dev/null 2>&1 || true
fi

echo
echo "Resolved Layers is installed."
echo "  Launch from the applications menu, or run: resolved-layers"
if ! printf '%s' ":$PATH:" | grep -q ":$BIN_DIR:"; then
  echo
  echo "Note: $BIN_DIR is not on your PATH. Add it to use the terminal command."
fi
echo
echo "No Model Package is installed, so prediction is unavailable."
echo "Supply one with --model-package MANIFEST.json once it is authorized."
