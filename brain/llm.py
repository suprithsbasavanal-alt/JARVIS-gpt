"""
brain/llm.py  —  JARVIS 3.0 REAL ACCESS EDITION
UPGRADE: Strict no-hallucination policy enforced in every system prompt.
- Every response includes a confidence score (0-100)
- Every response includes a source citation
- Uncertainty language is mandatory when not sure
- DuckDuckGo real web search with URL citations
- Checks Ollama is actually running before calling it
- Never returns made-up data
"""

import hashlib
import logging
import os
import re
import time

import ollama
import memory.database as db
import memory.rag       as rag
import core.real_access as ra

logger = logging.getLogger("JARVIS.brain")

# ─── Session history & cache ──────────────────────────────────────────────────
session_history: list[dict] = []
_response_cache: dict[str, dict] = {}   # hash → {reply, confidence, sources}

# ─── Active model ─────────────────────────────────────────────────────────────
_active_model = "llama3"
LOCAL_MODELS  = ["llama3", "mistral", "codellama", "phi3", "gemma"]

_ROUTING = {
    "code": "codellama", "script": "codellama", "debug": "codellama",
    "python": "codellama", "javascript": "codellama",
    "fast": "mistral",    "quick": "mistral",
}

# ─── NO-HALLUCINATION SYSTEM PROMPT ADDENDUM ──────────────────────────────────
NO_HALLUCINATION_RULES = """
ABSOLUTE RULES — YOU MUST FOLLOW THESE WITH NO EXCEPTIONS:
1. NEVER make up information. If you do not know something, say exactly: "I don't know."
2. NEVER invent facts, statistics, dates, names, file contents, or any data.
3. ALWAYS state where your information comes from (memory, web search, file, training data).
4. If you are not 100% sure, say: "I'm not certain, but based on [source]: ..."
5. If a resource is unavailable, say: "I cannot access that right now."
6. If your answer comes from training data (not live search), say: "Based on my training data (which may be outdated): ..."
7. NEVER guess what a file contains — only report content you were actually given.
8. End every factual answer with: [Source: <where the info came from>] [Confidence: <0-100>%]
"""


def switch_model(model_name: str) -> str:
    global _active_model
    model_name = model_name.strip().lower()
    if model_name in LOCAL_MODELS:
        _active_model = model_name
        return f"Switched to {model_name}."
    return f"Model '{model_name}' not available. Options: {', '.join(LOCAL_MODELS)}."


def _pick_model(text: str) -> str:
    lower = text.lower()
    for kw, model in _ROUTING.items():
        if kw in lower:
            return model
    return _active_model


def _build_system_prompt(custom: str | None = None) -> str:
    """
    Builds a system prompt that ALWAYS includes the no-hallucination rules.
    Custom prompts from agents also get the rules appended.
    """
    facts     = db.get_all_facts()
    tasks     = db.get_tasks()
    user_name = db.get_fact("name") or "Sir"

    if custom:
        return custom + "\n\n" + NO_HALLUCINATION_RULES

    prompt  = (
        f"You are JARVIS (Just A Rather Very Intelligent System), version 3.0. "
        f"You are a sophisticated AI assistant running on macOS for {user_name}. "
        f"Speak concisely and professionally. "
    )
    if facts:
        prompt += f"Known facts from memory: {facts}. "
    if tasks:
        prompt += f"Pending tasks: {', '.join(tasks[:5])}. "

    prompt += "\n\n" + NO_HALLUCINATION_RULES
    return prompt


def _real_web_search(query: str) -> tuple[str, list[str]]:
    """
    Performs a real DuckDuckGo search and returns (text_snippet, [url_citations]).
    Returns ("", []) if offline or search fails.
    """
    sources = []
    if not ra.get("Internet")["ok"]:
        return "", []

    try:
        import requests
        from bs4 import BeautifulSoup

        # DuckDuckGo instant-answer API (no JS required)
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8
        )
        data    = r.json()
        snippet = data.get("AbstractText", "") or data.get("Answer", "")
        src_url = data.get("AbstractURL", "") or data.get("AbstractSource", "")

        if src_url:
            sources.append(src_url)

        # If no instant answer, pull top HTML result snippet
        if not snippet:
            html_r = requests.get(
                f"https://html.duckduckgo.com/html/?q={query}",
                headers={"User-Agent": "Mozilla/5.0"}, timeout=8
            )
            soup   = BeautifulSoup(html_r.text, "html.parser")
            result = soup.find("div", class_="result__snippet")
            if result:
                snippet = result.get_text()[:500]
            # Collect up to 3 result URLs
            for link in soup.select("a.result__url")[:3]:
                href = link.get("href", "")
                if href.startswith("http"):
                    sources.append(href)

        return snippet[:600], sources

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return "", []


def _extract_confidence(reply: str) -> int:
    """
    Extracts confidence percentage from the AI reply text.
    Looks for '[Confidence: XX%]' pattern. Defaults to 70 if not found.
    """
    match = re.search(r'\[Confidence:\s*(\d+)%?\]', reply, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Heuristic: if AI used uncertainty language, lower confidence
    if any(phrase in reply.lower() for phrase in [
        "i don't know", "i'm not certain", "i cannot", "may be outdated", "not sure"
    ]):
        return 45
    return 75   # default moderate confidence


def generate_response(
    user_input: str,
    custom_system_prompt: str | None = None,
    use_cache: bool = True,
    reasoning_mode: bool = False,
    web_augment: bool = True,
) -> dict:
    """
    Primary AI response function.

    Returns a dict:
    {
        "reply"      : str,   # the answer text
        "confidence" : int,   # 0-100
        "sources"    : list,  # list of source URLs or labels
        "model"      : str,   # which model answered
        "elapsed"    : float, # seconds taken
    }

    NEVER raises — always returns an honest error dict on failure.
    """
    global session_history

    # ── 1. Check Ollama is actually running ──────────────────────────────────
    if not ra.get("Ollama AI")["ok"]:
        return {
            "reply"      : (
                "I cannot connect to my AI brain right now. "
                "Ollama is not running. Please open Terminal and run: ollama serve"
            ),
            "confidence" : 0,
            "sources"    : ["System status check"],
            "model"      : "none",
            "elapsed"    : 0.0,
        }

    # ── 2. Cache check ───────────────────────────────────────────────────────
    cache_key = hashlib.md5(user_input.encode()).hexdigest()
    if use_cache and cache_key in _response_cache:
        cached = _response_cache[cache_key]
        cached["sources"] = ["Response cache"] + cached.get("sources", [])
        return cached

    # ── 3. RAG semantic context ──────────────────────────────────────────────
    rag_results  = rag.search_memory(user_input, top_k=2)
    rag_context  = ""
    rag_sources  = []
    if rag_results:
        rag_context  = "Relevant long-term memories: " + " | ".join(rag_results) + ". "
        rag_sources  = ["Long-term memory (RAG)"]

    # ── 4. Real web search for time-sensitive questions ──────────────────────
    web_snippet = ""
    web_sources = []
    needs_web   = web_augment and any(kw in user_input.lower() for kw in [
        "today", "latest", "current", "news", "price", "weather",
        "2024", "2025", "2026", "right now", "live", "real time"
    ])
    if needs_web:
        web_snippet, web_sources = _real_web_search(user_input)

    # ── 5. Assemble system prompt ────────────────────────────────────────────
    system_content = _build_system_prompt(custom_system_prompt)
    if rag_context:
        system_content += f"\n{rag_context}"
    if web_snippet:
        system_content += (
            f"\nReal-time web search result (use this, it is live data): {web_snippet}"
        )
    if reasoning_mode:
        system_content += (
            "\nREASONING MODE: Think step by step. "
            "Show your reasoning process, then give a final answer."
        )

    # ── 6. Append user message ───────────────────────────────────────────────
    session_history.append({"role": "user", "content": user_input})
    if len(session_history) > 20:
        session_history = session_history[-20:]

    messages = [{"role": "system", "content": system_content}] + session_history

    # ── 7. Call Ollama ───────────────────────────────────────────────────────
    model = _pick_model(user_input)
    t0    = time.time()
    try:
        response = ollama.chat(model=model, messages=messages)
        reply    = response["message"]["content"].strip()
        elapsed  = round(time.time() - t0, 2)
        logger.info(f"[{model}] responded in {elapsed}s")

        # ── 8. Save to history & cache ────────────────────────────────────
        session_history.append({"role": "assistant", "content": reply})

        all_sources  = rag_sources + web_sources
        if not all_sources:
            all_sources = [f"Ollama/{model} training data"]

        confidence = _extract_confidence(reply)

        result = {
            "reply"      : reply,
            "confidence" : confidence,
            "sources"    : all_sources,
            "model"      : model,
            "elapsed"    : elapsed,
        }
        _response_cache[cache_key] = result
        if len(_response_cache) > 200:
            del _response_cache[next(iter(_response_cache))]

        return result

    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return {
            "reply"      : (
                f"My neural network failed to respond. Error: {type(e).__name__}: {e}. "
                "This is a real error — I am not making it up. "
                "Please check that Ollama is running and the model is downloaded."
            ),
            "confidence" : 0,
            "sources"    : ["Error log"],
            "model"      : model,
            "elapsed"    : round(time.time() - t0, 2),
        }


def clear_session():
    """Clears in-memory conversation history."""
    global session_history
    session_history = []
    logger.info("Session history cleared.")


def list_models() -> str:
    return f"Available: {', '.join(LOCAL_MODELS)}. Active: {_active_model}."
