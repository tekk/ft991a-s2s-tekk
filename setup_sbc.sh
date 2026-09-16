#!/usr/bin/env bash
# ==============================================================================
# YAESU FT-991A AI S2S BRIDGE - SBC SETUP SCRIPT
# Supports Raspberry Pi OS, Armbian, Ubuntu on Radxa, Orange Pi, FriendlyElec
# ==============================================================================

set -e

echo "=== [1/5] Checking and Installing System Packages ==="
if command -v apt-get &> /dev/null; then
    echo "Detected apt package manager. Installing required audio, serial & ffmpeg packages..."
    sudo apt-get update -y
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        libportaudio2 \
        portaudio19-dev \
        ffmpeg \
        alsa-utils
else
    echo "Notice: Non-Debian system detected. Please ensure ffmpeg and portaudio are installed."
fi

echo "=== [2/5] Setting User Permissions (dialout & audio) ==="
CURRENT_USER=$(whoami)
echo "Adding user '$CURRENT_USER' to dialout and audio groups for USB serial and sound card access..."
sudo usermod -a -G dialout,audio "$CURRENT_USER" || true

echo "=== [3/5] Setting Up Python Virtual Environment ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "=== [4/5] Building Frontend Static Assets ==="
if command -v npm &> /dev/null; then
    cd "$SCRIPT_DIR/frontend"
    npm install
    npm run build
    cd "$SCRIPT_DIR"
else
    echo "[WARN] Node/npm not detected. Pre-compiled assets must be present in frontend/dist."
fi

echo "=== [5/5] Setup Complete! ==="
echo "You can now launch the transceiver bridge with:"
echo "    ./run.sh --port 80"
echo ""
echo "Note: If you were just added to the 'dialout' or 'audio' groups, please log out"
echo "and log back in (or restart) for group permissions to take effect on /dev/ttyUSB*."
