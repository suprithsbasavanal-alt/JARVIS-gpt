#!/bin/bash
# ============================================================
# setup.sh  —  JARVIS 3.0 REAL ACCESS — One-Shot Setup Script
# Run this ONCE before starting JARVIS for the first time.
# Usage:  bash setup.sh
# ============================================================

set -e
PASS=0; FAIL=0

ok()   { echo "  ✅  $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌  $1"; FAIL=$((FAIL+1)); }
hdr()  { echo ""; echo "═══════════════════════════════════════"; echo "  $1"; echo "═══════════════════════════════════════"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   J.A.R.V.I.S. 3.0  —  SETUP SCRIPT     ║"
echo "║   Real-Access Edition                    ║"
echo "╚══════════════════════════════════════════╝"

# ─── 1. Python version ────────────────────────────────────────────────────────
hdr "1. Python"
if python3 --version 2>&1 | grep -q "3\.[1-9][0-9]"; then
    ok "Python 3.10+ found: $(python3 --version)"
else
    fail "Python 3.10+ required. Install from https://www.python.org/downloads/"
fi

# ─── 2. pip ───────────────────────────────────────────────────────────────────
hdr "2. pip"
if python3 -m pip --version &>/dev/null; then
    ok "pip available"
else
    fail "pip not found — run: python3 -m ensurepip"
fi

# ─── 3. Homebrew ──────────────────────────────────────────────────────────────
hdr "3. Homebrew"
if command -v brew &>/dev/null; then
    ok "Homebrew found: $(brew --version | head -1)"
else
    fail "Homebrew not found. Install from https://brew.sh"
fi

# ─── 4. Tesseract OCR ────────────────────────────────────────────────────────
hdr "4. Tesseract OCR"
if command -v tesseract &>/dev/null; then
    ok "Tesseract: $(tesseract --version 2>&1 | head -1)"
else
    echo "  Installing Tesseract via Homebrew..."
    brew install tesseract && ok "Tesseract installed" || fail "Tesseract install failed"
fi

# ─── 5. PortAudio (required for PyAudio) ─────────────────────────────────────
hdr "5. PortAudio (for microphone)"
if brew list portaudio &>/dev/null; then
    ok "PortAudio already installed"
else
    echo "  Installing PortAudio..."
    brew install portaudio && ok "PortAudio installed" || fail "PortAudio failed"
fi

# ─── 6. Ollama ────────────────────────────────────────────────────────────────
hdr "6. Ollama (local AI)"
if command -v ollama &>/dev/null; then
    ok "Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
else
    echo "  Ollama not found."
    echo "  Install from: https://ollama.ai  OR  brew install ollama"
    fail "Ollama not installed"
fi

# Check if Ollama server is running
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama server is running"
else
    echo "  Starting Ollama server in background..."
    ollama serve &>/dev/null &
    sleep 3
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        ok "Ollama server started"
    else
        fail "Ollama server failed to start — run 'ollama serve' manually"
    fi
fi

# Pull required models
hdr "6b. Ollama Models"
for model in llama3 nomic-embed-text; do
    if ollama list 2>/dev/null | grep -q "$model"; then
        ok "Model '$model' already downloaded"
    else
        echo "  Pulling $model (this may take a few minutes)..."
        ollama pull "$model" && ok "$model downloaded" || fail "$model download failed"
    fi
done

# ─── 7. Python venv ───────────────────────────────────────────────────────────
hdr "7. Python Virtual Environment"
if [ ! -d "venv" ]; then
    python3 -m venv venv && ok "venv created" || fail "venv creation failed"
else
    ok "venv already exists"
fi

source venv/bin/activate

# ─── 8. pip packages ──────────────────────────────────────────────────────────
hdr "8. Python Packages"
echo "  Installing from requirements.txt..."
pip install --upgrade pip -q
pip install -r requirements.txt -q && ok "All packages installed" || fail "Some packages failed — check output above"

# Test critical imports
for pkg in PyQt6 ollama pyaudio speech_recognition psutil requests bs4 pytesseract cv2; do
    if python3 -c "import $pkg" 2>/dev/null; then
        ok "import $pkg"
    else
        fail "Cannot import $pkg — try: pip install $pkg"
    fi
done

# ─── 9. Directory structure ───────────────────────────────────────────────────
hdr "9. Project Directories"
for dir in sounds sounds/cache configs logs core utils/real_files ui agents brain memory voice system automation vision; do
    mkdir -p "$dir" && ok "Directory: $dir"
done

# ─── 10. Permissions check ───────────────────────────────────────────────────
hdr "10. macOS Permissions"
echo ""
echo "  JARVIS needs the following permissions in:"
echo "  System Preferences → Security & Privacy → Privacy"
echo ""
echo "  [ ] Microphone        → allow Terminal"
echo "  [ ] Camera            → allow Terminal"
echo "  [ ] Screen Recording  → allow Terminal"
echo "  [ ] Accessibility     → allow Terminal"
echo "  [ ] Full Disk Access  → allow Terminal"
echo "  [ ] Calendars         → allow Terminal / JARVIS"
echo "  [ ] Contacts          → allow Terminal / JARVIS"
echo "  [ ] Reminders         → allow Terminal / JARVIS"
echo ""
echo "  Opening System Preferences..."
open "x-apple.systempreferences:com.apple.preference.security?Privacy"

# ─── 11. Environment variables ───────────────────────────────────────────────
hdr "11. Environment Variables"
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<EOF
# JARVIS 3.0 — Environment Variables
# Fill in your API keys below

PICOVOICE_API_KEY=your_key_from_console.picovoice.ai
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
OPENWEATHER_KEY=
JARVIS_CITY=London
NEWS_API_KEY=
EOF
    ok "Created .env template — fill in your API keys"
else
    ok ".env already exists"
fi

# ─── 12. Quick connectivity test ─────────────────────────────────────────────
hdr "12. Connectivity Tests"
if curl -s --max-time 3 https://1.1.1.1 &>/dev/null; then
    ok "Internet: connected"
else
    fail "Internet: offline"
fi

if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama API: responding"
else
    fail "Ollama API: not responding — run 'ollama serve'"
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
hdr "SETUP SUMMARY"
echo ""
echo "  ✅  Passed: $PASS"
echo "  ❌  Failed: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "  🎉  All checks passed! Start JARVIS with:"
    echo ""
    echo "      source venv/bin/activate"
    echo "      python3 main.py"
    echo ""
else
    echo "  ⚠️   Fix the $FAIL failing items above, then run:"
    echo ""
    echo "      source venv/bin/activate"
    echo "      python3 main.py"
    echo ""
    echo "  Each failure has instructions on how to fix it."
fi
