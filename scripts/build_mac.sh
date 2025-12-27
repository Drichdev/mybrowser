#!/usr/bin/env bash
set -euo pipefail

# Build script for macOS: creates MyBrowser.app and a DMG
# Requirements:
#  - pyinstaller installed in the venv
#  - sips, iconutil (macOS built-ins)
#  - assets/logo.icns or assets/logo.png (1024x1024 preferred)

APP_NAME="MyBrowser"
ASSETS_DIR="assets"
CONFIG_DIR="config"
ICON_ICNS="$ASSETS_DIR/logo.icns"
ICON_PNG="$ASSETS_DIR/logo.png"
DIST_DIR="dist"

echo "[1/4] Ensuring .icns icon exists..."
if [[ ! -f "$ICON_ICNS" ]]; then
  if [[ -f "$ICON_PNG" ]]; then
    echo " - $ICON_ICNS not found. Generating from $ICON_PNG"
    mkdir -p "$ASSETS_DIR/logo.iconset"
    sips -z 16 16     "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_16x16.png"
    sips -z 32 32     "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_16x16@2x.png"
    sips -z 32 32     "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_32x32.png"
    sips -z 64 64     "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_32x32@2x.png"
    sips -z 128 128   "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_128x128.png"
    sips -z 256 256   "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_128x128@2x.png"
    sips -z 256 256   "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_256x256.png"
    sips -z 512 512   "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_256x256@2x.png"
    sips -z 512 512   "$ICON_PNG" --out "$ASSETS_DIR/logo.iconset/icon_512x512.png"
    # Use original PNG as 1024x1024 when available
    if command -v sips >/dev/null 2>&1; then
      # If original not 1024, this still works for iconutil
      cp "$ICON_PNG" "$ASSETS_DIR/logo.iconset/icon_512x512@2x.png" 2>/dev/null || true
    fi
    iconutil -c icns "$ASSETS_DIR/logo.iconset" -o "$ICON_ICNS"
  else
    echo "ERROR: $ICON_ICNS not found and $ICON_PNG missing. Provide one of them."
    exit 1
  fi
else
  echo " - Found $ICON_ICNS"
fi

echo "[2/4] Running PyInstaller..."
pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --icon "$ICON_ICNS" \
  --add-data "assets:assets" \
  --add-data "config:config" \
  --collect-submodules PyQt5.QtWebEngine \
  --collect-data PyQt5.QtWebEngine \
  --hidden-import sip \
  main.py

APP_PATH="$DIST_DIR/$APP_NAME.app"
DMG_PATH="$DIST_DIR/$APP_NAME.dmg"

if [[ ! -d "$APP_PATH" ]]; then
  echo "ERROR: $APP_PATH not found. PyInstaller may have failed."
  exit 1
fi

echo "[3/4] Creating DMG..."
rm -f "$DMG_PATH" || true
hdiutil create -volname "$APP_NAME" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"

echo "[4/4] Done. Output:"
echo " - App: $APP_PATH"
echo " - DMG: $DMG_PATH"
