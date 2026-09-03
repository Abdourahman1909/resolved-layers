#!/usr/bin/env bash
# Remove a user-level Resolved Layers installation.
#
# This removes the isolated runtime, the launcher symlink, the installed icons,
# and the desktop entry. It never touches the local Run Archive, so persisted
# Verified Runs survive an uninstall and can be removed deliberately.

set -euo pipefail

APP_ID="org.computationalhealthlab.ResolvedLayers"

PREFIX="${PREFIX:-$HOME/.local}"
RUNTIME_DIR="${RUNTIME_DIR:-$PREFIX/opt/resolved-layers}"
BIN_DIR="$PREFIX/bin"
ICON_ROOT="$PREFIX/share/icons/hicolor"
DESKTOP_DIR="$PREFIX/share/applications"

echo "==> Removing the desktop entry"
rm -f "$DESKTOP_DIR/$APP_ID.desktop"

echo "==> Removing installed icons"
for size in 16 24 32 48 64 128 256 512; do
  rm -f "$ICON_ROOT/${size}x${size}/apps/$APP_ID.png"
done

echo "==> Removing the launcher"
rm -f "$BIN_DIR/resolved-layers"

echo "==> Removing the isolated runtime"
rm -rf "$RUNTIME_DIR"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$ICON_ROOT" >/dev/null 2>&1 || true
fi

echo
echo "Resolved Layers is removed."
echo "The local Run Archive was left untouched."
