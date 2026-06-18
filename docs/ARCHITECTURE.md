# System Architecture Document: Project JARVIS

This document contains the complete system architecture for JARVIS: a Personal Cognitive Operating System running locally on Apple Silicon macOS.

---

## 1. Layer Architecture

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

## 2. Component Diagram

```
       ┌────────────────────────┐
       │   React HUD Client     │
       └─────┬──────────▲───────┘
             │ (IPC)    │ (IPC)
       ┌─────▼──────────┴───────┐
       │ Electron Main Process  │
       └─────┬──────────▲───────┘
             │ (HTTP)   │ (WebSockets Streaming)
       ┌─────▼──────────┴───────┐
       │     FastAPI Router     │
       └─────┬──────────▲───────┘
             │          │
 ┌───────────▼──────────┴───────────────┐
 │         Executive Agent              │
 └─────┬──────────┬──────────────┬──────┘
       │          │              │
 ┌─────▼────┐ ┌───▼────┐ ┌───────▼──────┐
 │ Planner  │ │ Memory │ │ Specialized  │
 │ Agent    │ │ Agent  │ │ Agents       │
 └──────────┘ └───┬────┘ └───────┬──────┘
                  │              │
 ┌────────────────▼───────┐ ┌────▼───────────────────────────────────┐
 │     PostgreSQL DB      │ │ Tools System:                          │
 │     Qdrant Vector DB   │ │ - Web Search (DuckDuckGo HTML)         │
 │     Redis Cache        │ │ - Screen Capture & macOS Vision OCR    │
 └────────────────────────┘ │ - Automation Shell (AppleScript, Bash) │
                            └────┬───────────────────────────────────┘
                                 ▼ (Inference Router)
                            ┌────────────────────────────────────────┐
                            │    Ollama API Client (Qwen-2.5 / LLM)  │
                            └────────────────────────────────────────┘
```

---

## 3. Data Flow Diagram

```
[User Speech] ──► (Web Audio API Stream) ──► [WebSocket: /api/audio/stream]
                                                   │
                                                   ▼
                                            [Whisper STT]
                                                   │ (Transcribed Text)
                                                   ▼
                                           [Executive Agent]
                                                   │
     ┌─────────────────────────────────────────────┴──────────────────────────────────────────────┐
     ▼ (Get Context)                                                                               ▼ (Plan Tasks)
[Memory Agent]                                                                              [Planner Agent]
     │                                                                                             │
     ├──► Read Postgres (Episodic Sessions)                                                        ▼
     └──► Read Qdrant Vector (Factual Memory)                                               [Subtask list DAG]
                                                                                                   │
     ┌─────────────────────────────────────────────────────────────────────────────────────────────┤
     ▼ (Goal: Screen Read)                                                                         ▼ (Goal: File Organization)
[Vision Agent]                                                                              [Automation Agent]
     │                                                                                             │
     ├──► screencapture -x                                                                         ├──► Check Audit Log
     ├──► macOS Vision framework (Native OCR)                                                      ├──► Prompt Security Gate
     └──► Extract frontmost active application                                                     └──► Run osascript (AppleScript)
                                                                                                           │
                                                                                                           ▼
                                                                                                   [Response Synthesis]
                                                                                                           │
                                                                                                           ▼
                                                                                                     [Piper TTS]
                                                                                                           │
                                                                                                           ▼
                                                                                           [Speaker Output / HUD Screen]
```

---

## 4. Agent Architecture
The orchestrator operates as a Finite State Machine (FSM), controlling task scheduling, agent selection, and execution guardrails:

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

*   **ExecutiveAgent**: Receives raw prompts, fetches active window coordinates, requests semantic vectors from memory stores, runs coordination cycles, and synthesizes finalized spoken briefs.
*   **PlannerAgent**: Compiles goal lists. If a plan is not solvable by simple text responses, it returns a Directed Acyclic Graph (DAG) JSON detailing sequentially ordered subtasks, agent allocations, and dependencies.
*   **Specialized Agents**: Handlers for distinct execution scopes:
    *   **ResearchAgent**: Gathers web search data, extracts raw text, removes page noise, and validates credentials.
    *   **CodingAgent**: Formulates codebase modifications, analyzes error stack traces, and validates directory codebases.
    *   **VisionAgent**: Handles visual frames, coordinate calculations, and OCR extraction mapping.
    *   **AutomationAgent**: Writes shell inputs, calls AppleScript API routines, and modifies files.
    *   **MemoryAgent**: Tracks facts during conversations, indexes semantic vectors, and cleans database tables.

---

## 5. Memory Architecture
JARVIS maintains a multi-tiered memory system designed to separate fast cache states from long-term factual contexts:

```
                  ┌─────────────────────────────────────┐
                  │            USER INPUT               │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │         Working Memory Cache        │
                  │   - Redis / In-Memory Dict          │
                  │   - Active application focus state  │
                  │   - Screen coordinate layouts       │
                  └──────────────────┬──────────────────┘
                                     ▼
        ┌────────────────────────────┴────────────────────────────┐
        ▼ (Episodic Context Retrieval)                            ▼ (Semantic Context Retrieval)
┌────────────────────────────────┐                        ┌────────────────────────────────┐
│   Episodic Memory Database     │                        │   Semantic Vector Database     │
│   - PostgreSQL / SQLite        │                        │   - Qdrant Database            │
│   - Conversation transcripts   │                        │   - 1536-dimensional vectors   │
│   - Completed task statuses    │                        │   - User preferences           │
│   - Action audit log traces    │                        │   - Historical code structures │
│   - Ongoing project boards     │                        │   - Aggregated knowledge lists │
└────────────────────────────────┘                        └────────────────────────────────┘
```
*   **Sync Cycle**: The MemoryAgent runs a consolidation sweep every 5 turns. It reads recent episodic transcripts, extracts structural assertions (e.g. User prefers Dark Mode), writes them to PostgreSQL, creates embeddings, and updates the Qdrant index.

---

## 6. Research Architecture
To ensure factual accuracy and avoid hallucinations, the system routes search queries through a strict verification pipeline:

```
          ┌────────────────────────────────────────────────┐
          │                 Research Topic                 │
          └───────────────────────┬────────────────────────┘
                                  ▼
          ┌────────────────────────────────────────────────┐
          │             Query Expansion Engine             │
          │  - Generates multiple variant lookup strings   │
          └───────────────────────┬────────────────────────┘
                                  ▼
          ┌────────────────────────────────────────────────┐
          │             Web Search Coordinator             │
          │  - Requests DuckDuckGo HTML / Lite backends    │
          │  - Collects links, titles, and body snippets   │
          └───────────────────────┬────────────────────────┘
                                  ▼
          ┌────────────────────────────────────────────────┐
          │          Fact-Verification Engine              │
          │  - Cross-references data points across sources │
          │  - Separates consensus facts from speculation  │
          │  - Flags contradictions and discrepancies      │
          └───────────────────────┬────────────────────────┘
                                  ▼
          ┌────────────────────────────────────────────────┐
          │           Source Citation Compiler             │
          │  - Formulates final report with source links   │
          └────────────────────────────────────────────────┘
```

---

## 7. Voice Architecture
Voice synthesis and recognition are processed through local streaming pipelines:

```
[Microphone Audio (Raw PCM bytes)]
              │
              ▼
[Web Audio API Media Stream Node]
              │
              ▼ (WebSocket Transmission)
[/api/audio/stream Endpoint]
              │
              ├──────────► [Wake Word Detector (OpenWakeWord)] ──► Trigger Listen State
              │
              ▼
  [Whisper Speech-to-Text] ──► (Transcribed Text) ──► [Reasoning Engine]
                                                             │
                                                             ▼ (Output Text)
  [Piper Text-to-Speech] ◄───────────────────────────────────┘
              │
              ▼ (Generated WAV audio)
     [Audio Output Node]
```
*   **OpenWakeWord**: Constantly parses small overlapping audio buffers from the stream. If "Jarvis" is matched, it triggers the HUD client to flash electric-cyan and capture the subsequent command block.
*   **Speech-to-Text**: Whisper runs in the background. It transcribes audio buffers locally using CoreML bindings on macOS to minimize processor load.
*   **Text-to-Speech**: Piper parses response strings and generates real-time audio waveforms using custom voice model weights.

---

## 8. Automation Architecture
```
                      ┌──────────────────────────┐
                      │    Automation Agent      │
                      └────────────┬─────────────┘
                                   ▼
                      ┌──────────────────────────┐
                      │    Execution Router      │
                      └──────┬────────────┬──────┘
                             │            │
            ┌────────────────┘            └────────────────┐
            ▼ (Shell Execution)                            ▼ (macOS Desktop GUI API)
┌───────────────────────────────┐               ┌───────────────────────────────┐
│     POSIX Subprocess Shell    │               │      AppleScript Subsystem    │
│  - Executes terminal commands │               │  - Runs native osascript code │
│  - Captures stdout / stderr   │               │  - Targets active UI windows  │
│  - Enforces execution timeouts│               │  - Simulates keyboard presses │
└───────────────────────────────┘               └───────────────────────────────┘
```
*   **POSIX Subprocess Shell**: Safe, isolated execution commands with timeouts. Destructive operations are identified by pattern match and routed to the Security Gate.
*   **AppleScript Subsystem**: Used to control native macOS applications (Finder, Safari, Calendar, Reminders) without requiring third-party APIs.

---

## 9. Security Architecture
All system control commands are monitored by a strict security subsystem:

```
[Automation Agent Command Payload]
                │
                ▼
      [System Guard Filter]
                │
                ├── (Safe commands: directory listing, simple app launches)
                │         │
                │         ▼
                │   [Direct Run]
                │
                └── (Destructive/CLI commands: rm, write, brew install)
                          │
                          ▼
             [Pending Audit Database] ◄── (Writes is_approved=FALSE log)
                          │
                          ▼
             [HUD Authorization Request]
                          │
                          ▼ (Websocket / UI Approve Action)
              [Security Approver Gate] ──► (Sets is_approved=TRUE) ──► [Execute]
```
*   **Sandboxing Policy**: The Python server runs inside an environment restricted to specific directories. Any workspace modification requires registration in the database audit log.
*   **Credential Storage**: No passwords or API keys are stored in source code files. Keys are loaded at startup from environment variables or the native macOS Keychain.

---

## 10. Knowledge Architecture
The system coordinates structural developer knowledge, project rules, and codebase states into a unified context wrapper:

```
┌────────────────────────────────────────────────────────┐
  │                 Workspace Directory                    │
  └───────────────────────────┬────────────────────────────┘
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 Dynamic Workspace Parser               │
  │  - Maps repository file directory layout               │
  │  - Parses package configurations and dependencies      │
  │  - Builds code syntax indexes                          │
  └───────────────────────────┬────────────────────────────┘
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 RAG Context Pipeline                   │
  │  - Vectorizes code snippets, docs, and configs         │
  │  - Merges project settings with active goals           │
  └───────────────────────────┬────────────────────────────┘
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │               Unified Prompt Context                   │
  │  - Injects relevant files and codebase states          │
  │  - Adds local system guidelines & style rules          │
  └───────────────────────────┬────────────────────────────┘
                              ▼
                      [Executive Agent]
```
