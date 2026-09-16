#!/usr/bin/env bash
# ==============================================================================
# YAESU FT-991A AI S2S BRIDGE - FULL TEST SUITE RUNNER
# Runs both Backend (Pytest) and Web UI (Vitest) test suites.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================="
echo " [1/2] RUNNING BACKEND UNIT & INTEGRATION TESTS (PYTEST)"
echo "======================================================="
./venv/bin/pytest -v tests/

echo ""
echo "======================================================="
echo " [2/2] RUNNING WEB UI REACT COMPONENT TESTS (VITEST)"
echo "======================================================="
cd "$SCRIPT_DIR/frontend"
npm test

echo ""
echo "======================================================="
echo " >>> ALL BACKEND & WEB UI TESTS PASSED SUCCESSFULLY! <<<"
echo "======================================================="
