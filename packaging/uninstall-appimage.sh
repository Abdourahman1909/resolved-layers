#!/usr/bin/env bash
# Remove a Resolved Layers AppImage from the applications menu.
#
# Run it from anywhere:  ./uninstall-appimage.sh
#
# This removes the desktop entry and the installed icons. The AppImage file
# itself and the local Run Archive are left alone, so persisted Verified Runs
# survive and the application can still be run directly.

set -euo pipefail

APP_ID="org.computationalhealthlab.ResolvedLayers"
PREFIX="${PREFIX:-$HOME/.local}"
ICON_ROOT="$PREFIX/share/icons/hicolor"
DESKTOP_DIR="$PREFIX/share/applications"

echo "==> Removing the desktop entry"
rm -f "$DESKTOP_DIR/$APP_ID.desktop"

echo "==> Removing installed icons"
for size in 16 24 32 48 64 128 256 512; do
  rm -f "$ICON_ROOT/${size}x${size}/apps/$APP_ID.png"
done

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
  gtk-update-icon-cache -f -t "$ICON_ROOT" >/dev/null 2>&1 || true

echo
echo "Removed from the applications menu."
echo "The AppImage file and the local Run Archive were left untouched."
