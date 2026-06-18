# JARVIS: Personal Cognitive Operating System

JARVIS is a local-first, privacy-focused Personal Cognitive Operating System designed to run locally on macOS Apple Silicon. It manages strategic goals, projects, contextual memory, and automates desktop interactions using a multi-agent orchestration pattern.

---

## 1. Directory Structure

```
/JARVIS-gpt
├── apps/
│   └── hud-client/            # Electron + React HUD Presentation Layer
├── backend/                   # FastAPI reasoning core and services
│   ├── app/
│   │   ├── api/               # API endpoints (e.g. memory CRUD)
│   │   ├── core/              # Config, DB, and cache wrappers
│   │   ├── services/          # Modular subsystem controllers
│   │   │   ├── memory/        # Postgres/Qdrant memory fabric
│   │   │   ├── pcc/           # Cognitive state PKG engine
│   │   │   ├── executive/     # Query routing & priority score engines
│   │   │   └── voice/         # Audio transcription & TTS hooks
│   │   └── agents/            # Goal planning and execution agents
│   └── tests/                 # Pytest test suites
├── docker-compose.yml         # Container definitions for Postgres/Qdrant/Redis
├── docs/                      # Specification and architecture docs
└── .env.example               # Configuration example settings
```

---

## 2. Quickstart & Local Development

### Prerequisites
* macOS with Apple Silicon (M1/M2/M3/M4)
* Python 3.10+
* Node.js 18+ & npm
* Docker Desktop (Optional; falls back to SQLite/In-memory cache when unavailable)

### 1. Setup Backend
1. Copy the configuration template:
   ```bash
   cp .env.example backend/app/core/.env
   ```
2. Navigate to `backend/`, create a virtual environment, and install dependencies:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:
   ```bash
   python -m uvicorn backend.app.main:app --port 8000 --reload
   ```

### 2. Launch HUD Client
1. Navigate to `apps/hud-client/`:
   ```bash
   cd apps/hud-client
   npm install
   ```
2. Run in development mode:
   ```bash
   npm run dev
   ```

---

## 3. Running Unit Tests
To execute the backend service and memory fabric unit test suite:
```bash
cd backend
source .venv/bin/activate
pytest tests/
```
