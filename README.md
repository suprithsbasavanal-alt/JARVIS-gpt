# J.A.R.V.I.S. 3.0 ULTIMATE
### Just A Rather Very Intelligent System — Mac AI Assistant

> **Version 3.0** | Built with Python + PyQt6 + Ollama + RAG + Multi-Agent Architecture

---

## 🚀 Quick Start

```bash
# 1. Install Python 3.11+  (https://www.python.org/downloads/)

# 2. Install Ollama  (https://ollama.ai)
brew install ollama
ollama serve &          # start in background
ollama pull llama3      # required — primary model
ollama pull mistral     # optional — fast model
ollama pull codellama   # optional — coding model
ollama pull nomic-embed-text  # required for RAG memory

# 3. Install Tesseract OCR (for screen reading)
brew install tesseract

# 4. Clone / open the project
cd /path/to/JARVIS

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install all dependencies
pip install -r requirements.txt

# 7. Run JARVIS
python3 main.py
```

---

## 🗣️ Voice Commands Reference

### App Control
| Say | Action |
|-----|--------|
| `Open Chrome` | Launches Google Chrome |
| `Open VS Code` | Launches Visual Studio Code |
| `Open Terminal` | Launches Terminal |
| `Close Spotify` | Quits the named app |
| `Open website github.com` | Opens URL in Chrome |

### System Control
| Say | Action |
|-----|--------|
| `Set volume 50` | Sets volume to 50% |
| `Mute` / `Unmute` | Mutes or unmutes audio |
| `Lock screen` | Locks the Mac |
| `Take a screenshot` | Saves screenshot to Desktop |
| `System stats` | Reports CPU / RAM / Battery |
| `Battery` | Reports battery level |
| `Turn on WiFi` / `Turn off WiFi` | Toggles Wi-Fi |

### Memory
| Say | Action |
|-----|--------|
| `Remember my name is Arjun` | Saves a fact |
| `Remember to buy groceries` | Adds a task |
| `What are my tasks?` | Lists pending tasks |
| `Deeply remember [text]` | Saves to semantic RAG memory |
| `Remind me to [task] at 09:00` | Sets a timed reminder |

### Automation Modes
| Say | Action |
|-----|--------|
| `Start study mode` | Opens Notes, YouTube lofi, Spotify, vol 40 |
| `Start coding mode` | Opens VS Code, Terminal, GitHub, vol 30 |
| `Start movie mode` | Opens VLC, vol 80, dims screen |
| `Start sleep mode` | Mutes, sleeps Mac |
| `Start gym mode` | Opens Spotify, vol 85 |
| `List modes` | Shows all available modes |
| `Create a new mode called [name]` | Creates a custom mode |

### Vision AI
| Say | Action |
|-----|--------|
| `Read my screen` | OCR + AI summary of current screen |
| `Explain this error` | Reads screen, finds and explains errors |

### AI Brain
| Say | Action |
|-----|--------|
| `Switch to mistral` | Changes active AI model |
| `Translate [text] to Hindi` | Translates using AI |
| `Solve [math problem]` | Step-by-step math solver |
| `Tech news` | Latest technology headlines |
| `Daily briefing` | Weather + tasks + reminders summary |
| `Start pomodoro` | 25-min focus timer with voice alerts |
| `I completed my workout` | Logs habit + shows streak |

---

## 🔧 Configuration

### Environment Variables (optional but recommended)
```bash
export PICOVOICE_API_KEY="your_key_from_console.picovoice.ai"
export ELEVENLABS_API_KEY="your_eleven_labs_key"
export ELEVENLABS_VOICE_ID="voice_id"
export OPENWEATHER_KEY="your_openweathermap_key"
export JARVIS_CITY="Mumbai"   # your city for weather
```

Create a `.env` file in the project root and `python-dotenv` will load it automatically.

---

## 🛠️ Architecture

```
JARVIS/
├── main.py              ← Entry point + command router
├── ui/hud.py            ← Cinematic 60fps PyQt6 HUD
├── brain/llm.py         ← Multi-model AI brain + cache + DuckDuckGo
├── voice/
│   ├── listener.py      ← Wake word + speech-to-text
│   └── speaker.py       ← ElevenLabs + macOS say TTS
├── memory/
│   ├── database.py      ← SQLite: facts, tasks, habits, reminders, notes
│   └── rag.py           ← Semantic RAG with local embeddings
├── agents/
│   ├── master_agent.py  ← 7-agent router
│   ├── coding_agent.py  ← Coding specialist
│   └── research_agent.py← Research specialist
├── system/mac_control.py← Full macOS control
├── automation/modes.py  ← 8 built-in + custom modes
├── vision/screen_reader.py ← OCR + screenshot
└── utils/
    ├── internet.py      ← Weather + search
    └── file_system.py   ← File finder + reader
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Ollama connection refused` | Run `ollama serve` in Terminal |
| `llama3 not found` | Run `ollama pull llama3` |
| `Microphone not working` | Grant mic permission in System Preferences → Privacy |
| `pytesseract error` | Run `brew install tesseract` |
| `PyAudio install fails` | Run `brew install portaudio` first |
| `pvporcupine key error` | Get free key at console.picovoice.ai |
| Wake word not working | Add `PICOVOICE_API_KEY` env var or use fallback mode |
| ElevenLabs silent | Set `ELEVENLABS_API_KEY` env var; JARVIS falls back to macOS `say` |

All errors are logged to `jarvis_log.txt` with full timestamps.

---

## 📦 What's New in v3.0

- 🎨 **Cinematic HUD** — 6-ring arc reactor, particle field, audio visualizer, typewriter text
- 🧠 **Multi-model brain** — Auto-routes to best model per question type
- 🌐 **DuckDuckGo search** — Answers current-events questions
- 💾 **Enhanced memory** — Habits, reminders, notes, pomodoro log
- 🤖 **7 specialised agents** — Coding, Research, Pomodoro, Habits, Translation, Math, News
- 🎙️ **ElevenLabs TTS** — Ultra-realistic voice with emotion detection
- 🖥️ **30+ Mac commands** — Clipboard, notifications, Spotlight, Finder, stats
- ⏰ **Daily briefing** — Auto-runs at 09:00 with weather + tasks
- 🔔 **Reminder poller** — Fires due reminders every 60 seconds
- 🔒 **Graceful shutdown** — "Goodbye JARVIS" saves state and exits cleanly

---

*JARVIS 3.0 ULTIMATE — Built for macOS*
