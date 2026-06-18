# Product Requirements Document (PRD): Project JARVIS

## 1. Product Vision
JARVIS is a **Personal Cognitive Operating System** designed to function as a lifelong AI companion and digital chief of staff. Operating as a local-first, privacy-enclosed agent on Apple Silicon, JARVIS shifts human-AI interaction away from transactional message-response cycles. Instead, it maintains persistent awareness of user priorities, schedules, screen states, and file structures. The system autonomously plans tasks, executes deep fact-checked research, manages long-term goals, and controls the macOS environment, creating a highly personalized, context-aware operational partner.

---

## 2. Core Principles
*   **Local-First Enclave**: All personal data, documents, vector memories, and reasoning logs remain strictly on the host Mac, ensuring complete user privacy and zero data leakage.
*   **Verify-Before-Answer**: Factual queries are never answered through speculative model weights alone. The system executes web lookups, cross-references sources, detects discrepancies, and builds consensus before responding.
*   **Brevity and Executive Voice**: Communication is clean, concise, and direct. JARVIS avoids conversational filler, robotic meta-commentary, and unnecessary explanations.
*   **Proactive System Synthesis**: Rather than waiting for specific CLI commands, JARVIS continuously monitors projects, tracks milestones, analyzes screen states, and offers contextual solutions.
*   **Contextual Continuity**: Every query is evaluated against persistent episodic memory, user preferences, and the current desktop visual layout.

---

## 3. User Scenarios
*   **Daily Briefing**: The user starts their day, wakes JARVIS, and asks: *"Jarvis, give me a run-down."* JARVIS retrieves calendar events, active goals, coding project progress, and compiles a concise 3-bullet executive brief.
*   **Fact-Checked Research**: The user asks about a recent breaking development in AI. JARVIS triggers the Research Agent, queries multiple search endpoints, removes duplicates, identifies the consensus points, highlights contradictions, and synthesizes a verified report with source citations.
*   **Active Context Awareness**: While the user is editing code, JARVIS analyzes the screen via Vision OCR, cross-references the active file context, tracks the task progress, and proactively alerts them about outstanding test failures or architectural notes from a previous session.
*   **Secure Desktop Automation**: The user requests: *"Clean up my downloads folder and organize files by project."* JARVIS plans the file organization steps, displays the plan on the HUD interface, registers the audit logs, and executes safe shell movements once approved.

---

## 4. Functional Requirements & Priorities
| Requirement | Description | Priority |
|---|---|---|
| Natural Voice Loop | Continuous local wake-word detection ("Jarvis") and smooth speech response loop with interruptibility. | High |
| Verify-Reason-Answer | Web search cross-referencing, contradiction detection, and fact verification before answering. | High |
| Persistent Memory System | PostgreSQL relational episodic storage combined with Qdrant vector databases for long-term habits and preferences. | High |
| Desktop & File Control | AppleScript and terminal shell execution for macOS automation and directory management. | Medium |
| Screen Visual OCR | Zero-permission app detection (`lsappinfo`) combined with local Apple Vision OCR frame analysis. | Medium |
| Telemetry HUD UI | Translucent macOS HUD desktop window displaying reasoning traces and active agent tasks. | High |
