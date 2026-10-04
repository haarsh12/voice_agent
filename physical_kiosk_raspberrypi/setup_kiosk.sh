#!/bin/bash
# ==============================================================================
# Sahayak AI - Raspberry Pi Systemd & Hardware Auto-Start Installer
# Configures backend service and full screen kiosk mode on boot
# ==============================================================================

set -e

echo "⚙️ Setting up Sahayak AI Raspberry Pi Kiosk Services..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install system dependencies if missing
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-numpy python3-opencv alsa-utils espeak-ng unclutter chromium-browser

# Create systemd service for Kiosk Server
SERVICE_FILE="/etc/systemd/system/sahayak-kiosk.service"

sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=Sahayak AI Kiosk Server and Hardware Service
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/kiosk_server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable sahayak-kiosk.service
sudo systemctl restart sahayak-kiosk.service

# Setup LXDE / Wayfire autostart for Chromium Kiosk
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat <<EOF > "$AUTOSTART_DIR/sahayak-kiosk.desktop"
[Desktop Entry]
Type=Application
Name=Sahayak AI Kiosk
Exec=/bin/bash $SCRIPT_DIR/start_kiosk.sh
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$SCRIPT_DIR/start_kiosk.sh"

echo "✅ Sahayak AI Raspberry Pi Kiosk installed successfully!"
echo "Server status: sudo systemctl status sahayak-kiosk.service"
