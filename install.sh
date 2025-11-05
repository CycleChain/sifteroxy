#!/usr/bin/env bash
# Quick installation script for sifteroxy

set -euo pipefail

APP_DIR="/opt/sifteroxy"
SERVICE_NAME="sifteroxy"
CURRENT_USER="${SUDO_USER:-$USER}"

echo "Installing sifteroxy..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -U requests "requests[socks]"
else
    echo "Error: pip3 not found. Please install Python 3 and pip first."
    exit 1
fi

# Create application directory
echo "Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/metrics"
mkdir -p "$APP_DIR/logs"

# Copy files
echo "Copying files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/sifteroxy.py" "$APP_DIR/"
cp "$SCRIPT_DIR/sources.json" "$APP_DIR/"
cp "$SCRIPT_DIR/proxy_update.sh" "$APP_DIR/"
chmod +x "$APP_DIR/proxy_update.sh"
chmod +x "$APP_DIR/sifteroxy.py"

# Install systemd service and timer
echo "Installing systemd service and timer..."
cp "$SCRIPT_DIR/sifteroxy.service" "/etc/systemd/system/"
cp "$SCRIPT_DIR/sifteroxy.timer" "/etc/systemd/system/"

# Set ownership
chown -R "$CURRENT_USER:$CURRENT_USER" "$APP_DIR"

# Reload systemd
systemctl daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "To activate the timer, run:"
echo "  sudo systemctl enable --now sifteroxy.timer"
echo ""
echo "Or use the convenience script:"
echo "  sudo ./active.sh"
echo ""
echo "To check status:"
echo "  sudo systemctl status sifteroxy.timer"
echo "  sudo systemctl status sifteroxy.service"

