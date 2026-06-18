#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Clear terminal screen
clear

echo "=========================================================="
echo "      JARVIS // PERSONAL COGNITIVE OPERATING SYSTEM       "
echo "=========================================================="
echo "Starting FastAPI Backend and Electron HUD Client..."
echo ""

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend server
echo "[1/2] Launching FastAPI Backend Server..."
cd "$DIR/backend"
source .venv/bin/activate
python -m uvicorn backend.app.main:app --port 8000 --reload > /tmp/jarvis_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be online
echo "Waiting for backend port 8000 to be responsive..."
until curl -s http://localhost:8000/ > /dev/null; do
  sleep 0.5
done
echo "FastAPI Backend is ONLINE (PID: $BACKEND_PID)"
echo ""

# Start Electron HUD client
echo "[2/2] Launching Electron HUD Client..."
cd "$DIR/apps/hud-client"
npm run dev &
CLIENT_PID=$!

echo "=========================================================="
echo "JARVIS is now fully active."
echo "Press [CTRL+C] at any time to shut down all processes."
echo "=========================================================="

# Handle shutdown cleanly on Ctrl+C
cleanup() {
  echo ""
  echo "Shutting down JARVIS..."
  kill $BACKEND_PID || true
  kill $CLIENT_PID || true
  echo "All processes terminated cleanly."
  exit 0
}

trap cleanup INT

# Keep script running to monitor logs or wait for exit
wait
