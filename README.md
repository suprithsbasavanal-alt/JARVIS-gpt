# JARVIS AI Assistant - Ultimate Edition

A fully-featured, Iron Man-inspired AI assistant built entirely in Python.
Designed specifically for macOS. It is completely beginner-friendly, modular, and extensively documented.

## Features Included
1. **Core AI**: Wake word detection, Speech-to-text, and local AI processing via Ollama (Llama 3).
2. **Mac Automation**: Open/close apps, control volume, open websites, shutdown/lock screen.
3. **Memory System**: Persistent SQLite database to remember your name, facts, and pending tasks.
4. **Futuristic UI**: A dark-mode, neon-bordered, transparent floating HUD with real-time CPU/RAM stats.
5. **Vision AI**: Screen reading using Tesseract OCR to explain errors, and basic webcam face detection.
6. **Internet & Productivity**: Live weather, YouTube/Google search, and built-in Pomodoro focus timers.

## Folder Structure
- `main.py`: The entry point that boots up JARVIS.
- `brain/`: AI generation using Ollama (Llama 3).
- `voice/`: Speech-to-text (SpeechRecognition/Porcupine) and Text-to-speech (pyttsx3).
- `ui/`: Futuristic PyQt6 Iron Man HUD.
- `automation/`: Pre-programmed workflows (Study mode, Coding mode).
- `memory/`: SQLite database for persistent memory (tasks, names, facts).
- `vision/`: Screen reading, OCR, and Webcam face detection.
- `system/`: Mac application control, volume, lock screen, and CPU/RAM monitoring.
- `utils/`: Internet search, weather, and Pomodoro timers.

## Installation Steps

1. **Install System Dependencies (Mac Terminal):**
   ```bash
   brew install portaudio
   brew install tesseract
   ```

2. **Install Ollama:**
   Download from [ollama.com](https://ollama.com/) and run:
   ```bash
   ollama run llama3
   ```
   *Keep the app running in your menu bar.*

3. **Get Picovoice Wake Word Key:**
   Go to [Picovoice Console](https://console.picovoice.ai/), create a free account, copy your AccessKey, and paste it into `voice/listener.py` (line 12). This is required for the "Hey Jarvis" wake word.

4. **Install Python Packages:**
   Navigate to the project folder and run:
   ```bash
   pip3 install -r requirements.txt
   ```

## Running JARVIS
```bash
python3 main.py
```

## Example Commands
- "Jarvis, open Chrome."
- "Start coding mode."
- "What is the weather?"
- "Read my screen and explain this error."
- "Remember my name is Tony."
- "Who is in front of the computer?"
- "Lock the screen."
