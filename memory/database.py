"""
memory/database.py  —  JARVIS 3.0 ULTIMATE
UPGRADE v3.0:
- Added habits table (habit tracker with streaks)
- Added reminders table (with due_at timestamps)
- Added notes table (auto-categorised by topic)
- Added pomodoro_log table (focus session records)
- Added helper: auto_extract_facts() — passive memory from natural speech
- All connections use context managers for safety
"""

import sqlite3
import os
import datetime
import re
import logging

logger = logging.getLogger("JARVIS.memory.db")

# Database lives in the project root
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "jarvis_memory.db")


def _conn():
    """Returns an open SQLite connection. Always use with 'with' blocks."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Creates all required tables if they do not already exist.
    Safe to call multiple times (idempotent).
    """
    with _conn() as conn:
        c = conn.cursor()

        # Key-value facts (name, preferences, etc.)
        c.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # To-do tasks
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                task       TEXT,
                status     TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Full conversation log
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                role       TEXT,
                content    TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Habit tracker
        c.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT UNIQUE,
                streak       INTEGER DEFAULT 0,
                last_checked TEXT
            )
        """)

        # Reminders with due time
        c.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                message   TEXT,
                due_at    TEXT,
                done      INTEGER DEFAULT 0
            )
        """)

        # Smart notes
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT,
                content    TEXT,
                category   TEXT DEFAULT 'general',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pomodoro focus sessions
        c.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                duration   INTEGER,
                label      TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
    logger.info("Database initialised.")


# ─── FACTS ────────────────────────────────────────────────────────────────────

def save_fact(key: str, value: str):
    """Saves or updates a fact (key-value pair) in persistent memory."""
    with _conn() as conn:
        conn.execute(
            "REPLACE INTO facts (key, value) VALUES (?, ?)",
            (key.strip().lower(), str(value).strip())
        )
        conn.commit()
    logger.debug(f"Fact saved: {key} = {value}")


def get_fact(key: str) -> str | None:
    """Retrieves a fact by key. Returns None if not found."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT value FROM facts WHERE key = ?", (key.strip().lower(),)
        ).fetchone()
    return row[0] if row else None


def get_all_facts() -> str:
    """Returns all stored facts as a comma-separated string for the AI context."""
    with _conn() as conn:
        rows = conn.execute("SELECT key, value FROM facts").fetchall()
    return ", ".join(f"{k}: {v}" for k, v in rows) if rows else ""


def delete_fact(key: str):
    """Removes a fact from memory by key."""
    with _conn() as conn:
        conn.execute("DELETE FROM facts WHERE key = ?", (key.strip().lower(),))
        conn.commit()


# ─── TASKS ────────────────────────────────────────────────────────────────────

def add_task(task_text: str):
    """Adds a new pending task to the to-do list."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO tasks (task) VALUES (?)", (task_text.strip(),)
        )
        conn.commit()
    logger.debug(f"Task added: {task_text}")


def get_tasks() -> list[str]:
    """Returns a list of all pending task strings."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT task FROM tasks WHERE status = 'pending'"
        ).fetchall()
    return [r[0] for r in rows]


def complete_task(task_text: str):
    """Marks the first matching pending task as done."""
    with _conn() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'done' WHERE task LIKE ? AND status = 'pending'",
            (f"%{task_text}%",)
        )
        conn.commit()


# ─── HABITS ───────────────────────────────────────────────────────────────────

def log_habit(name: str) -> int:
    """
    Logs that the user completed a habit today.
    Increments streak if last completion was yesterday, resets otherwise.
    Returns the current streak count.
    """
    today = datetime.date.today().isoformat()
    with _conn() as conn:
        row = conn.execute(
            "SELECT streak, last_checked FROM habits WHERE name = ?", (name,)
        ).fetchone()

        if row is None:
            # New habit — start streak at 1
            conn.execute(
                "INSERT INTO habits (name, streak, last_checked) VALUES (?, 1, ?)",
                (name, today)
            )
            streak = 1
        else:
            streak, last = row
            yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
            if last == yesterday:
                streak += 1   # continuing streak
            elif last == today:
                pass           # already logged today — no change
            else:
                streak = 1     # streak broken
            conn.execute(
                "UPDATE habits SET streak = ?, last_checked = ? WHERE name = ?",
                (streak, today, name)
            )
        conn.commit()
    logger.debug(f"Habit '{name}' logged — streak: {streak}")
    return streak


def get_habits() -> list[tuple]:
    """Returns list of (name, streak, last_checked) for all habits."""
    with _conn() as conn:
        return conn.execute("SELECT name, streak, last_checked FROM habits").fetchall()


# ─── REMINDERS ────────────────────────────────────────────────────────────────

def add_reminder(message: str, due_at: str):
    """
    Adds a reminder.

    Args:
        message: The reminder text.
        due_at:  ISO datetime string, e.g. '2026-05-17 09:00'.
    """
    with _conn() as conn:
        conn.execute(
            "INSERT INTO reminders (message, due_at) VALUES (?, ?)",
            (message, due_at)
        )
        conn.commit()
    logger.debug(f"Reminder added: '{message}' at {due_at}")


def get_due_reminders() -> list[str]:
    """Returns all reminders whose due_at has passed and are not yet done."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, message FROM reminders WHERE due_at <= ? AND done = 0",
            (now,)
        ).fetchall()
        # Mark them as done
        for row_id, _ in rows:
            conn.execute("UPDATE reminders SET done = 1 WHERE id = ?", (row_id,))
        conn.commit()
    return [r[1] for r in rows]


# ─── NOTES ────────────────────────────────────────────────────────────────────

def save_note(title: str, content: str, category: str = "general"):
    """Saves a new note with an optional category."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO notes (title, content, category) VALUES (?, ?, ?)",
            (title, content, category)
        )
        conn.commit()
    logger.debug(f"Note saved: '{title}' [{category}]")


def search_notes(query: str) -> list[tuple]:
    """Full-text search on notes title and content."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT title, content, category, created_at FROM notes "
            "WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC LIMIT 5",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
    return rows


# ─── POMODORO ─────────────────────────────────────────────────────────────────

def log_pomodoro(duration_minutes: int, label: str = "Focus"):
    """Records a completed Pomodoro focus session."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO pomodoro_log (duration, label) VALUES (?, ?)",
            (duration_minutes, label)
        )
        conn.commit()
    logger.debug(f"Pomodoro logged: {duration_minutes}m — {label}")


# ─── PASSIVE MEMORY EXTRACTION ────────────────────────────────────────────────

# Patterns to auto-extract facts from natural speech
_EXTRACT_PATTERNS = [
    (r"my name is (\w+)",           "name"),
    (r"i am (\d+) years old",       "age"),
    (r"i live in ([a-z ]+)",        "location"),
    (r"i work at ([a-z ]+)",        "workplace"),
    (r"i am a ([a-z ]+)",           "profession"),
    (r"my favourite ([a-z]+) is ([a-z0-9 ]+)", None),  # generic key-value
    (r"i have a (.+) exam on (.+)",  None),             # reminder extraction
]


def auto_extract_facts(text: str):
    """
    Passively scans a user utterance for recognisable personal facts
    and saves them without the user explicitly saying 'remember'.
    """
    lower = text.lower()
    for pattern, key in _EXTRACT_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            if key:
                value = match.group(1)
                save_fact(key, value)
                logger.info(f"Auto-extracted fact: {key} = {value}")
            else:
                # Generic two-group pattern
                groups = match.groups()
                if len(groups) == 2:
                    save_fact(groups[0].strip(), groups[1].strip())
                    logger.info(f"Auto-extracted: {groups[0]} = {groups[1]}")
