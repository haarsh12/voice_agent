#!/bin/bash
# ==============================================================================
# Sahayak AI - Raspberry Pi Kiosk Chromium Autostart Script
# Launches full-screen kiosk browser pointing to localhost hardware app
# ==============================================================================

set -e

KIOSK_URL="http://localhost:5000"

# Hide cursor when idle
unclutter -idle 0.5 -root &

# Disable power saving and screen blanking
xset s off
xset s noblank
xset -dpms

# Suppress Chromium crash / restore bars
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences 2>/dev/null || true
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences 2>/dev/null || true

echo "🚀 Launching Chromium Kiosk on Raspberry Pi Touch Screen..."

chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --autoplay-policy=no-user-gesture-required \
  --check-for-update-interval=31536000 \
  --disable-component-update \
  --touch-events=enabled \
  --enable-features=OverlayScrollbar \
  --window-size=1024,600 \
  --window-position=0,0 \
  "$KIOSK_URL"
