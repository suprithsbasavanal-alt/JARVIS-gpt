"""
automation/modes.py  —  JARVIS 3.0 ULTIMATE
UPGRADE v3.0:
- All original modes upgraded with volume + browser URL steps
- New modes: Gym, Creative, Research, Night Owl
- Custom mode creation and persistence to JSON
- Mode listing command
- Each mode action is individually try-excepted so one failure doesn't halt the rest
"""

import os
import json
import time
import logging

import system.mac_control as mac
import voice.speaker as speaker

logger = logging.getLogger("JARVIS.automation.modes")

# Path to save user-defined custom modes
CUSTOM_MODES_PATH = os.path.join(os.path.dirname(__file__), "..", "configs", "custom_modes.json")

# Ensure the configs directory exists
os.makedirs(os.path.dirname(CUSTOM_MODES_PATH), exist_ok=True)


# ─── BUILT-IN MODE DEFINITIONS ────────────────────────────────────────────────
# Each mode is a dict with 'message' and 'steps' (list of callables).
# Using lambdas keeps each step short and readable.

BUILTIN_MODES = {

    "study": {
        "message": "Study mode activated. Good luck, Sir.",
        "steps": [
            lambda: mac.open_app("Notes"),
            lambda: mac.open_website("https://www.youtube.com/results?search_query=lofi+music"),
            lambda: mac.open_app("Spotify"),
            lambda: mac.set_volume(40),
            lambda: mac.send_notification("JARVIS", "Study Mode Active 📚"),
        ],
    },

    "coding": {
        "message": "Coding mode ready. Let's build something great.",
        "steps": [
            lambda: mac.open_app("Visual Studio Code"),
            lambda: mac.open_app("Terminal"),
            lambda: mac.open_website("https://github.com"),
            lambda: mac.set_volume(30),
            lambda: mac.send_notification("JARVIS", "Coding Mode Active 💻"),
        ],
    },

    "movie": {
        "message": "Enjoy your movie, Sir.",
        "steps": [
            lambda: mac.open_app("VLC") or mac.open_app("TV"),   # fallback to Apple TV
            lambda: mac.set_volume(80),
            lambda: mac.dim_screen(),
            lambda: mac.send_notification("JARVIS", "Movie Mode Active 🎬"),
        ],
    },

    "sleep": {
        "message": "Goodnight, Sir. Shutting everything down.",
        "steps": [
            lambda: mac.set_volume(0),
            lambda: mac.mute(),
            lambda: mac.send_notification("JARVIS", "Sleep Mode — Goodnight 🌙"),
            lambda: time.sleep(2),
            lambda: mac.sleep_mac(),
        ],
    },

    "gym": {
        "message": "Gym mode activated. Time to crush it!",
        "steps": [
            lambda: mac.open_app("Spotify"),
            lambda: mac.set_volume(85),
            lambda: mac.send_notification("JARVIS", "Gym Mode — Let's Go! 💪"),
        ],
    },

    "creative": {
        "message": "Creative mode on. Let your imagination flow.",
        "steps": [
            lambda: mac.open_app("Notion") or mac.open_app("Notes"),
            lambda: mac.open_website("https://www.are.na"),
            lambda: mac.set_volume(45),
            lambda: mac.send_notification("JARVIS", "Creative Mode Active 🎨"),
        ],
    },

    "research": {
        "message": "Research mode engaged. Deep dive incoming.",
        "steps": [
            lambda: mac.open_website("https://scholar.google.com"),
            lambda: mac.open_website("https://arxiv.org"),
            lambda: mac.open_app("Notes"),
            lambda: mac.set_volume(25),
            lambda: mac.send_notification("JARVIS", "Research Mode Active 🔬"),
        ],
    },

    "night owl": {
        "message": "Night owl mode on. Dark theme and low volume.",
        "steps": [
            lambda: mac.set_volume(20),
            lambda: mac.open_app("Notes"),
            lambda: mac.send_notification("JARVIS", "Night Owl Mode 🦉"),
        ],
    },
}


def activate_mode(command_text: str) -> str:
    """
    Detects which mode was requested from the command text and executes it.
    Checks built-in modes first, then user-defined custom modes.

    Args:
        command_text: The full voice command string (lowercased).

    Returns:
        A confirmation string.
    """
    lower = command_text.lower()

    # Detect mode name from command
    mode_name = None
    for name in list(BUILTIN_MODES.keys()) + list(_load_custom_modes().keys()):
        if name in lower:
            mode_name = name
            break

    if not mode_name:
        return "I did not recognise a mode name in that command."

    # Check built-in
    if mode_name in BUILTIN_MODES:
        return _run_mode(mode_name, BUILTIN_MODES[mode_name])

    # Check custom
    custom = _load_custom_modes()
    if mode_name in custom:
        return _run_custom_mode(mode_name, custom[mode_name])

    return f"Mode '{mode_name}' not found."


def _run_mode(name: str, mode_def: dict) -> str:
    """Executes each step of a built-in mode with individual error handling."""
    logger.info(f"Activating mode: {name}")
    for i, step in enumerate(mode_def["steps"]):
        try:
            step()
            time.sleep(0.3)   # small delay between actions
        except Exception as e:
            logger.error(f"Mode '{name}' step {i} failed: {e}")
    return mode_def.get("message", f"{name.title()} mode activated.")


def _run_custom_mode(name: str, actions: list) -> str:
    """Executes a custom mode stored as a list of action strings."""
    logger.info(f"Activating custom mode: {name}")
    results = []
    for action in actions:
        try:
            result = _execute_action_string(action)
            results.append(result)
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"Custom mode action failed: {e}")
    return f"Custom mode '{name}' activated."


def _execute_action_string(action: str) -> str:
    """
    Parses a plain-English action string saved in a custom mode and executes it.
    Supports: 'open <app>', 'set volume <n>', 'open website <url>'.
    """
    import re
    a = action.strip().lower()
    if a.startswith("open website"):
        url = a.replace("open website", "").strip()
        return mac.open_website(url)
    elif a.startswith("open"):
        app = a.replace("open", "").strip().title()
        return mac.open_app(app)
    elif "volume" in a:
        nums = re.findall(r"\d+", a)
        if nums:
            return mac.set_volume(int(nums[0]))
    return f"Unknown action: {action}"


# ─── CUSTOM MODE PERSISTENCE ──────────────────────────────────────────────────

def _load_custom_modes() -> dict:
    """Loads user-defined modes from the JSON file."""
    if not os.path.exists(CUSTOM_MODES_PATH):
        return {}
    try:
        with open(CUSTOM_MODES_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load custom modes: {e}")
        return {}


def _save_custom_modes(modes: dict):
    """Saves user-defined modes to the JSON file."""
    try:
        with open(CUSTOM_MODES_PATH, "w") as f:
            json.dump(modes, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save custom modes: {e}")


def create_custom_mode(name: str, actions: list) -> str:
    """
    Saves a new custom mode by name.

    Args:
        name:    The mode name, e.g. 'morning routine'.
        actions: List of plain-English action strings.

    Returns:
        Confirmation string.
    """
    modes = _load_custom_modes()
    modes[name.lower()] = actions
    _save_custom_modes(modes)
    logger.info(f"Custom mode saved: {name}")
    return f"I have saved the '{name}' mode with {len(actions)} actions."


def list_modes() -> str:
    """Returns a string listing all available modes."""
    builtin = list(BUILTIN_MODES.keys())
    custom  = list(_load_custom_modes().keys())
    all_modes = builtin + custom
    return "Available modes: " + ", ".join(m.title() for m in all_modes) + "."
