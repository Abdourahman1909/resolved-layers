#!/usr/bin/env bash
# Add a Resolved Layers AppImage to the applications menu.
#
# An AppImage runs by itself, but nothing registers it with the desktop, so it
# never appears when you search for it. This copies the AppImage to a stable
# location, installs its icons, and writes a desktop entry pointing at it.
#
# It needs only the AppImage. No repository checkout and no administrator
# rights are required.
#
#   ./install-appimage.sh Resolved_Layers-0.1.0-x86_64.AppImage
#
# Remove it again with uninstall-appimage.sh.

set -euo pipefail

APP_ID="org.computationalhealthlab.ResolvedLayers"
PREFIX="${PREFIX:-$HOME/.local}"
APPDIR="${APPIMAGE_DIR:-$HOME/Applications}"
ICON_ROOT="$PREFIX/share/icons/hicolor"
DESKTOP_DIR="$PREFIX/share/applications"

SOURCE="${1:-}"
if [ -z "$SOURCE" ] || [ ! -f "$SOURCE" ]; then
  echo "Usage: $(basename "$0") /path/to/Resolved_Layers-<version>-x86_64.AppImage" >&2
  exit 1
fi

SOURCE="$(cd "$(dirname "$SOURCE")" && pwd)/$(basename "$SOURCE")"
TARGET="$APPDIR/$(basename "$SOURCE")"

echo "==> Placing the AppImage in $APPDIR"
mkdir -p "$APPDIR"
if [ "$SOURCE" != "$TARGET" ]; then
  cp "$SOURCE" "$TARGET"
fi
chmod +x "$TARGET"

echo "==> Installing application icons"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# The AppImage carries its own icons, so this needs no repository checkout.
( cd "$WORK" && "$TARGET" --appimage-extract "usr/share/icons/*" >/dev/null 2>&1 ) || true

installed_icons=0
for size in 16 24 32 48 64 128 256 512; do
  icon="$WORK/squashfs-root/usr/share/icons/hicolor/${size}x${size}/apps/$APP_ID.png"
  [ -f "$icon" ] || continue
  target="$ICON_ROOT/${size}x${size}/apps"
  mkdir -p "$target"
  cp "$icon" "$target/$APP_ID.png"
  installed_icons=$((installed_icons + 1))
done
if [ "$installed_icons" -eq 0 ]; then
  echo "    no icons found inside the AppImage; the menu entry will use a generic icon" >&2
else
  echo "    $installed_icons sizes installed"
fi

echo "==> Registering the desktop entry"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/$APP_ID.desktop" <<ENTRY
[Desktop Entry]
Type=Application
Version=1.0
Name=Resolved Layers
GenericName=Variant Inference
Comment=Evidence-first desktop inference for missense-variant pathogenicity
Exec="$TARGET" %f
TryExec=$TARGET
Icon=$APP_ID
Terminal=false
Categories=Science;Biology;MedicalSoftware;
Keywords=variant;genomics;pathogenicity;inference;evidence;
MimeType=text/csv;
StartupNotify=true
StartupWMClass=Resolved Layers
ENTRY
chmod 644 "$DESKTOP_DIR/$APP_ID.desktop"

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
  gtk-update-icon-cache -f -t "$ICON_ROOT" >/dev/null 2>&1 || true

echo
echo "Resolved Layers is in your applications menu."
echo "  AppImage: $TARGET"
echo
echo "Keep the AppImage where it is. The menu entry points at that exact path,"
echo "so moving or deleting the file breaks the entry."
