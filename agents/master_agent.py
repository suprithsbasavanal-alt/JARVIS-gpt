"""
agents/master_agent.py  —  JARVIS 3.0 ULTIMATE
UPGRADE v3.0:
- Added PomodoroAgent, HabitAgent, TranslationAgent, MathAgent, NewsAgent
- Added model-switch command detection
- Added confidence routing: complex questions use reasoning_mode
- All routing heuristics documented
"""

import logging
import brain.llm as llm
from agents.coding_agent   import CodingAgent
from agents.research_agent import ResearchAgent

logger = logging.getLogger("JARVIS.master_agent")


class PomodoroAgent:
    """Manages 25-min work / 5-min break Pomodoro sessions with voice announcements."""

    def start(self) -> str:
        """Starts a Pomodoro timer in a background thread."""
        import threading, time
        import voice.speaker as speaker
        import memory.database as db

        def run_session():
            speaker.speak("Pomodoro started. 25 minutes of deep focus begins now.", block=True)
            time.sleep(25 * 60)     # 25 minutes
            speaker.speak("Time is up. Take a 5-minute break.", block=True)
            db.log_pomodoro(25, "Focus session")
            time.sleep(5 * 60)      # 5-minute break
            speaker.speak("Break over. Ready for the next session?", block=True)

        t = threading.Thread(target=run_session, daemon=True)
        t.start()
        return "Pomodoro timer started. I will announce when it is time to break."


class HabitAgent:
    """Handles habit tracking commands."""

    def log(self, habit_name: str) -> str:
        import memory.database as db
        streak = db.log_habit(habit_name)
        if streak == 1:
            return f"Logged '{habit_name}'. New habit started! Keep it up."
        elif streak >= 7:
            return f"Incredible! You are on a {streak}-day streak for '{habit_name}'. Outstanding dedication."
        else:
            return f"Great job! Your '{habit_name}' streak is now {streak} days."

    def show(self) -> str:
        import memory.database as db
        habits = db.get_habits()
        if not habits:
            return "No habits tracked yet. Tell me what habits you want to build."
        lines = [f"{name}: {streak} day streak" for name, streak, _ in habits]
        return "Here are your habits: " + "; ".join(lines) + "."


class TranslationAgent:
    """Translates text to a target language using the AI brain."""

    def translate(self, text: str, target_lang: str) -> str:
        prompt = f"Translate the following text to {target_lang}. Only return the translated text, nothing else: '{text}'"
        return llm.generate_response(prompt)


class MathAgent:
    """Solves mathematical problems step by step."""

    def solve(self, problem: str) -> str:
        prompt = (
            f"Solve this mathematical problem step by step: {problem}. "
            f"Show each step clearly. Give the final answer at the end."
        )
        return llm.generate_response(prompt, reasoning_mode=True)


class NewsAgent:
    """Fetches and summarises top news headlines."""

    def get_headlines(self, topic: str = "technology") -> str:
        """Fetches news headlines using DuckDuckGo search."""
        try:
            import requests
            url = "https://api.duckduckgo.com/"
            params = {
                "q"       : f"{topic} news today",
                "format"  : "json",
                "no_html" : 1,
            }
            r = requests.get(url, params=params, timeout=8)
            data = r.json()
            topics = data.get("RelatedTopics", [])[:5]
            lines = []
            for t in topics:
                if isinstance(t, dict) and "Text" in t:
                    lines.append(t["Text"][:120])
            if lines:
                return "Here are the latest headlines: " + ". ".join(lines)
            return "I could not fetch news at this time."
        except Exception as e:
            logger.error(f"NewsAgent error: {e}")
            return "News fetch failed. Please check your internet connection."


class MasterAgent:
    """
    The central cognitive router for JARVIS.
    Analyses the user's intent via keyword heuristics and delegates to
    the most appropriate specialised sub-agent or the general LLM.
    """

    def __init__(self):
        self.coding     = CodingAgent()
        self.research   = ResearchAgent()
        self.pomodoro   = PomodoroAgent()
        self.habit      = HabitAgent()
        self.translator = TranslationAgent()
        self.math       = MathAgent()
        self.news       = NewsAgent()

    def process_request(self, user_input: str) -> str:
        """
        Routes the user's request to the correct agent.
        Priority order: model-switch > coding > pomodoro > habit > translate > math > news > research > general
        """
        lower = user_input.lower()
        logger.info(f"MasterAgent routing: '{user_input[:60]}…'")

        # ── Model switch ───────────────────────────────────────────────────────
        if "switch to" in lower:
            for model in ["llama3", "mistral", "codellama", "phi3", "gemma"]:
                if model in lower:
                    return llm.switch_model(model)

        # ── Coding ────────────────────────────────────────────────────────────
        if any(kw in lower for kw in [
            "code", "script", "python", "javascript", "html", "css",
            "debug", "function", "class", "fix this", "write a program"
        ]):
            logger.debug("→ Coding Agent")
            return self.coding.execute(user_input)

        # ── Pomodoro ──────────────────────────────────────────────────────────
        if any(kw in lower for kw in ["pomodoro", "focus timer", "work session", "25 minute"]):
            logger.debug("→ Pomodoro Agent")
            return self.pomodoro.start()

        # ── Habit ─────────────────────────────────────────────────────────────
        if any(kw in lower for kw in ["completed my", "finished my", "did my", "habit"]):
            import re
            match = re.search(r"(completed|finished|did) my (.+)", lower)
            if match:
                return self.habit.log(match.group(2).strip())
            return self.habit.show()

        # ── Translation ───────────────────────────────────────────────────────
        if "translate" in lower:
            import re
            lang_match = re.search(r"to (\w+)", lower)
            target_lang = lang_match.group(1) if lang_match else "Hindi"
            text = re.sub(r"translate.*?to \w+", "", lower).strip()
            logger.debug(f"→ Translation Agent [{target_lang}]")
            return self.translator.translate(text or user_input, target_lang)

        # ── Math ──────────────────────────────────────────────────────────────
        if any(kw in lower for kw in [
            "calculate", "solve", "what is", "integral", "derivative",
            "equation", "math", "calculus", "statistics"
        ]):
            logger.debug("→ Math Agent")
            return self.math.solve(user_input)

        # ── News ──────────────────────────────────────────────────────────────
        if any(kw in lower for kw in ["news", "headlines", "latest tech", "current events"]):
            topic = "technology"
            for t in ["sports", "science", "politics", "finance", "health", "ai"]:
                if t in lower:
                    topic = t
                    break
            logger.debug(f"→ News Agent [{topic}]")
            return self.news.get_headlines(topic)

        # ── Research / explanation ────────────────────────────────────────────
        if any(kw in lower for kw in [
            "research", "explain", "summarise", "summarize",
            "find out", "who is", "what is", "how does", "why does"
        ]):
            logger.debug("→ Research Agent")
            return self.research.execute(user_input)

        # ── General conversational brain (with reasoning for long questions) ──
        reasoning = len(user_input.split()) > 15   # use CoT for complex queries
        logger.debug(f"→ General Brain [reasoning={reasoning}]")
        return llm.generate_response(user_input, reasoning_mode=reasoning)


# Global singleton used by main.py
master = MasterAgent()
