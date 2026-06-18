# System Architecture Document: Project JARVIS (Version 1.0)

This document contains the master system architecture for JARVIS: a Personal Cognitive Operating System running locally on Apple Silicon macOS.

---

## 1. Unified System Topology

The diagram below outlines the overall data routing across the core layers and cognitive engines:

```
[User Speech/Text] ──► [Sensory Input Layer] ──► [Executive Mind (Priority/Attention)]
                                                      │
         ┌────────────────────────────────────────────┴────────────────────────────────────────────┐
         ▼ (Retrieve Identity / Principles)                                                         ▼ (Retrieve Knowledge Graphs)
[Identity Engine]                                                                           [Personal Cognitive Core]
         │                                                                                         │
         ├──► Values & Motivation Models                                                           ├──► Cognitive State (Focus State)
         └──► Future Self Growth Vector                                                            └──► Semantic Property Graph Walks
                                                                                                           │
         ┌─────────────────────────────────────────────────────────────────────────────────────────┘
         ▼
[Planning Engine] ──► [Agents Scheduler] ──► [Tools & Automation] ──► [Verification] ──► [Response Synthesis]
```

---

## 2. Layer Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT PRESENTATION LAYER                       │
│  - React Holographic HUD (Stitch Design System Tokens)                 │
│  - Electron Preload Bridge (Secure Context Isolation, Safe IPC IPC)    │
│  - Electron Main Process (Window Management, Native Vibrancy, Hooks)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼ (WebSockets / REST IPC)
┌────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION & BACKEND LAYER                     │
│  - FastAPI Web Server (Endpoints, Routers, Middlewares)                 │
│  - Executive Coordinator Agent & Task Scheduler                        │
│  - Tool Registry & AppleScript / Shell Execution Subsystems            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼ (Local API / Metal Shaders)
┌────────────────────────────────────────────────────────────────────────┐
│                        LOCAL INFERENCE & STORE                         │
│  - Ollama Server (Llama-3, Qwen-2.5 local model routing)               │
│  - Whisper STT (PCM streaming)   - Piper TTS / macOS say               │
│  - PostgreSQL (Episodic Store)   - Qdrant (High-dim Vector DB)         │
│  - Redis Container (Cache)                                             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼ (Syscalls / Darwin Core APIs)
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE OPERATING SYSTEM LAYER                     │
│  - macOS Darwin Kernel & POSIX System Calls                            │
│  - Apple Event Manager (AppleScript / osascript execution)             │
│  - Quartz Window Services & Vision Framework (Native OCR Engine)       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼ (Hardware System Architecture)
┌────────────────────────────────────────────────────────────────────────┐
│                            HARDWARE LAYER                              │
│  - Apple Silicon M4 System-on-Chip (Unified Memory, GPU, AMX, CPU)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cognitive Subsystems

### 3.1 Identity Engine (IE)
The **Identity Engine** operates at the top of the cognitive loop, establishing who the user is and where their growth targets lie.
*   **Values Model**: Tracks preferred choices and trade-offs (e.g. Local Privacy vs. Cloud Convenience).
*   **Future Self Model**: Maintains long-term aspirational skills, target timeframes, and growth focuses.
*   **Evolution Algorithm**: Decays short-term interests while elevating recurring behaviors into core identity nodes based on temporal duration and reinforcement counts.

### 3.2 Executive Mind (EM)
The **Executive Mind** acts as the high-level Chief of Staff, managing attention allocation, scheduling priority tasks, and identifying project bottlenecks.
*   **Priority Score**:
    $$Priority = \alpha \cdot Impact + \beta \cdot Urgency - \gamma \cdot Cost$$
*   **Attention Drift Auditor**: Evaluates actual window focus logs against planned attention allocations to flag defocus.
*   **Daily Strategic Briefing**: Automatically consolidates yesterday's timeline milestones and builds a concise 3-bullet priority schedule.

### 3.3 Personal Cognitive Core (PCC)
The **Personal Cognitive Core** maintains a representation of active projects, repositories, window states, and concept links.
*   **Personal Knowledge Graph (PKG)**: Links user nodes (Identity, Preferences, Goals, Skills, Projects) using semantic properties.
*   **Cognitive State Engine**: Tracks focus indicators, application contexts, and fatigue metrics.
*   **Memory Consolidation Loop**: Periodically reads episodic chat logs and screen extractions to merge fresh assertions into Qdrant and Postgres databases.

---

## 4. Agent Architecture

The orchestrator executes task plans using a Finite State Machine (FSM) scheduling DAG task blocks:

```
          ┌─────────────────┐
          │   User Query    │
          └────────┬────────┘
                   ▼
       ┌───────────────────────┐
       │   Planner (Task DAG)  │
       └───────────┬───────────┘
                   ▼
  ┌─────────► [Task Loop] ◄──────────┐
  │                │                 │
  │                ▼                 │
  │     ┌─────────────────────┐      │
  │     │   Agent Dispatch    │      │
  │     └──────────┬──────────┘      │
  │                ▼                 │
  │     ┌─────────────────────┐      │
  │     │   Tool Execution    │      │
  │     └──────────┬──────────┘      │
  │                ▼                 │
  │     ┌─────────────────────┐      │
  │     │ Safety / Audit Gate ├──────┤ (Denied / Safety Failure)
  │     └──────────┬──────────┘      │
  │                ▼                 │
  │     ┌─────────────────────┐      │
  │     │  Memory Injection   │      │
  │     └──────────┬──────────┘      │
  │                ▼                 │
  └───────── [Task Finished] ────────┘
                   │ (DAG Complete)
                   ▼
        ┌─────────────────────┐
        │ Response Synthesis  │
        └─────────────────────┘
```

*   **Research Agent**: Conducts web scrapes via DuckDuckGo HTML, removes duplicates, cross-references sources, and flags contradictions.
*   **Coding Agent**: Designs directories, writes functional diff blocks, and debugs compilation logs.
*   **Vision Agent**: Captures screen layouts, queries frontmost applications via `lsappinfo`, and runs native macOS Vision OCR.
*   **Automation Agent**: Controls directories, compiles AppleScript layouts, and triggers macOS actions safely.

---

## 5. Security & Isolation Design

1.  **Permission Gate**: Destructive shell operations or workspace writes are added to the database with `is_approved = FALSE` and held until authorized via HUD websocket callbacks.
2.  **API Secrets Enclave**: Credentials remain locally in `backend/.env` or inside the macOS system keychain, never leaking to frontend assets or external servers.
3.  **Local Sandboxing**: Network access is restricted to search engines.
