#!/bin/bash
set -e

SERVICE_NAME="pico-chime"
INSTALL_DIR="/opt/pico-chime"
MODULE_NAME="chime"
SERVICE_FILE_SOURCE="$(dirname "$0")/${SERVICE_NAME}.service"
SERVICE_FILE_TARGET="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON_BIN="/usr/bin/python3"

echo "🚀 Setting up Pico Chime..."

# 1. Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

# 2. Create the installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
  echo "📁 Creating installation directory at $INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
fi

# 3. Copy the chime module to /opt/pico-chime/
if [ -d "$MODULE_NAME" ]; then
  echo "📦 Copying module '$MODULE_NAME' to $INSTALL_DIR"
  rm -rf "$INSTALL_DIR/$MODULE_NAME"
  cp -r "$MODULE_NAME" "$INSTALL_DIR/"
else
  echo "❌ Cannot find module directory '$MODULE_NAME' in $(pwd)"
  exit 1
fi

# 4. Copy the systemd service file to /etc/systemd/system/
if [ -f "$SERVICE_FILE_SOURCE" ]; then
  echo "⚙️ Installing systemd service file to $SERVICE_FILE_TARGET"
  cp "$SERVICE_FILE_SOURCE" "$SERVICE_FILE_TARGET"
else
  echo "❌ Cannot find service file at $SERVICE_FILE_SOURCE"
  exit 1
fi

# 5. Reload systemd and enable/start the service
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

echo "✅ Enabling Pico Chime service..."
systemctl enable "$SERVICE_NAME"

echo "▶️ Starting Pico Chime service..."
systemctl restart "$SERVICE_NAME"

# 6. Show the current service status
systemctl status "$SERVICE_NAME" --no-pager

echo "🎉 Setup complete! The Pico Chime service is running."
