#!/usr/bin/env bash
# ==============================================================================
# YAESU FT-991A AI S2S BRIDGE - LAUNCH SCRIPT
# Usage:
#   ./run.sh                  (Defaults to port 80 with >10000 fallback)
#   ./run.sh --port 8080      (Specific port)
#   ./run.sh --mock           (Hardware simulation mode without physical radio)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure virtualenv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating and installing dependencies..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Activate virtualenv
source venv/bin/activate

# Execute FastAPI backend and console UI
exec python3 -m backend.app "$@"
