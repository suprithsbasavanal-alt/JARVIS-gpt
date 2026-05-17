# JARVIS AI Assistant for Mac

Welcome to your personal JARVIS! This is a complete, beginner-friendly AI assistant built with Python.

## Prerequisites
Before installing the Python packages, you need to install some system dependencies. Open your Terminal and run these commands:

1. **Install Homebrew** (if you don't have it):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install PortAudio** (needed for microphone access):
   ```bash
   brew install portaudio
   ```

3. **Install Tesseract** (needed for screen reading):
   ```bash
   brew install tesseract
   ```

4. **Install Ollama** (the AI brain):
   Download and install from [ollama.com](https://ollama.com/)
   After installing, open Terminal and run:
   ```bash
   ollama run llama3
   ```
   *Keep this running or make sure Ollama app is open in your Mac menu bar.*

5. **Get Picovoice AccessKey** (for wake word):
   - Go to [Picovoice Console](https://console.picovoice.ai/)
   - Create a free account and copy your AccessKey.
   - Open `main.py` and replace `"YOUR_PICOVOICE_ACCESS_KEY_HERE"` with your real key.

## Installation

1. Open Terminal and navigate to this folder:
   ```bash
   cd "/Users/suprith.s.basavanal/Documents/antigrativity /JARVIS"
   ```

2. Install all required Python libraries:
   ```bash
   pip3 install -r requirements.txt
   ```

## Running JARVIS
Once everything is installed, run:
```bash
python3 main.py
```

## Common Errors
- **PyAudio fails to install**: Make sure you ran `brew install portaudio` first. If it still fails, try `pip install global pyaudio`.
- **Microphone not working**: Go to Mac System Settings -> Privacy & Security -> Microphone and ensure Terminal (or your IDE) has permission.
- **Ollama connection error**: Make sure the Ollama app is running and you have downloaded the `llama3` model.
- **Wake Word Error**: Ensure you pasted your Picovoice AccessKey into `main.py`.
