"""
core/real_access.py  —  JARVIS 3.0 REAL ACCESS SYSTEM
Manages live connection status for every data source.
Every test actually probes the real service — no assumed states.
Status is refreshed every 5 seconds in a background thread.
"""

import threading
import time
import os
import subprocess
import socket
import logging
import shutil
from datetime import datetime

logger = logging.getLogger("JARVIS.real_access")

# ─── STATUS REGISTRY ──────────────────────────────────────────────────────────
# Each key maps to a dict: {status, last_checked, message}
_status: dict = {}
_lock   = threading.Lock()


def _set(name: str, ok: bool, msg: str = ""):
    """Thread-safe status update."""
    with _lock:
        _status[name] = {
            "ok"           : ok,
            "message"      : msg,
            "last_checked" : datetime.now().strftime("%H:%M:%S"),
        }


def get_all() -> dict:
    """Returns a copy of the full status registry."""
    with _lock:
        return dict(_status)


def get(name: str) -> dict:
    """Returns status for a single source, or unknown if not yet tested."""
    with _lock:
        return _status.get(name, {"ok": False, "message": "Not yet tested", "last_checked": "—"})


# ─── INDIVIDUAL PROBES ────────────────────────────────────────────────────────

def _probe_ollama():
    """Checks if Ollama HTTP server is responding on localhost:11434."""
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        msg = f"Models: {', '.join(models)}" if models else "Running but no models pulled"
        _set("Ollama AI", True, msg)
    except Exception as e:
        _set("Ollama AI", False, f"Offline — run 'ollama serve' in Terminal ({e})")


def _probe_internet():
    """Real internet connectivity check — tries to reach 1.1.1.1 (Cloudflare)."""
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("1.1.1.1", 53))
        _set("Internet", True, "Connected")
    except Exception:
        _set("Internet", False, "No internet — JARVIS cannot fetch live data")


def _probe_microphone():
    """Checks if at least one input audio device is accessible via pyaudio."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        count = pa.get_device_count()
        pa.terminate()
        if count > 0:
            _set("Microphone", True, f"{count} audio device(s) found")
        else:
            _set("Microphone", False, "No audio input devices found")
    except Exception as e:
        _set("Microphone", False, f"pyaudio error: {e}")


def _probe_screen_capture():
    """
    Tests screen capture by running screencapture to /tmp and checking if the file appeared.
    Requires Screen Recording permission in System Preferences → Privacy.
    """
    try:
        test_path = "/tmp/jarvis_test_cap.png"
        result = subprocess.run(
            ["screencapture", "-x", "-t", "png", test_path],
            timeout=5, capture_output=True
        )
        if os.path.exists(test_path):
            size = os.path.getsize(test_path)
            os.remove(test_path)
            if size > 1000:   # real screenshot is always > 1 KB
                _set("Screen Capture", True, "Screen Recording permission granted")
            else:
                _set("Screen Capture", False, "Screenshot empty — grant Screen Recording in System Preferences → Privacy")
        else:
            _set("Screen Capture", False, "screencapture failed — grant Screen Recording permission")
    except Exception as e:
        _set("Screen Capture", False, f"Error: {e}")


def _probe_webcam():
    """Tries to open webcam with OpenCV (device 0)."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ok  = cap.isOpened()
        cap.release()
        if ok:
            _set("Webcam", True, "Camera accessible")
        else:
            _set("Webcam", False, "Camera not found or permission denied — check System Preferences → Privacy → Camera")
    except Exception as e:
        _set("Webcam", False, f"OpenCV error: {e}")


def _probe_filesystem():
    """Confirms read/write access to the home directory."""
    try:
        home = os.path.expanduser("~")
        test_file = os.path.join(home, ".jarvis_fs_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        _set("File System", True, f"Full read/write access to {home}")
    except Exception as e:
        _set("File System", False, f"Permission error: {e} — enable Full Disk Access in System Preferences")


def _probe_weather_api():
    """Tests OpenWeatherMap API if key is set."""
    key  = os.getenv("OPENWEATHER_KEY", "")
    city = os.getenv("JARVIS_CITY", "London")
    if not key:
        _set("Weather API", False, "Set OPENWEATHER_KEY environment variable")
        return
    try:
        import requests
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": key, "units": "metric"}, timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            _set("Weather API", True, f"{data['weather'][0]['description'].title()}, {data['main']['temp']}°C in {city}")
        else:
            _set("Weather API", False, f"API error {r.status_code}: {r.text[:80]}")
    except Exception as e:
        _set("Weather API", False, f"Request failed: {e}")


def _probe_spotify():
    """Checks if Spotify is running via AppleScript."""
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to (name of processes) contains "Spotify"'],
            capture_output=True, text=True, timeout=5
        )
        running = "true" in result.stdout.lower()
        if running:
            _set("Spotify", True, "Spotify is running")
        else:
            _set("Spotify", False, "Spotify not running — open Spotify first")
    except Exception as e:
        _set("Spotify", False, f"AppleScript error: {e}")


def _probe_calendar():
    """Tests Calendar access via AppleScript."""
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Calendar" to get name of calendars'],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0 and result.stdout.strip():
            _set("Calendar", True, f"Calendars: {result.stdout.strip()[:80]}")
        else:
            _set("Calendar", False, f"Calendar access denied — grant in System Preferences → Privacy → Calendars. Error: {result.stderr[:60]}")
    except Exception as e:
        _set("Calendar", False, f"AppleScript error: {e}")


def _probe_contacts():
    """Tests Contacts access via AppleScript."""
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Contacts" to get count of people'],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0:
            count = result.stdout.strip()
            _set("Contacts", True, f"{count} contacts accessible")
        else:
            _set("Contacts", False, "Contacts access denied — grant in System Preferences → Privacy → Contacts")
    except Exception as e:
        _set("Contacts", False, f"Error: {e}")


def _probe_tesseract():
    """Checks if Tesseract OCR binary is installed."""
    path = shutil.which("tesseract")
    if path:
        try:
            r = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=5)
            version = r.stdout.split("\n")[0]
            _set("Tesseract OCR", True, version)
        except Exception:
            _set("Tesseract OCR", True, f"Found at {path}")
    else:
        _set("Tesseract OCR", False, "Not installed — run: brew install tesseract")


def _probe_system_stats():
    """Tests psutil availability."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        _set("System Stats", True, f"Live CPU: {cpu}%")
    except Exception as e:
        _set("System Stats", False, f"psutil error: {e} — run: pip install psutil")


def _probe_news_api():
    """Tests NewsAPI key if configured."""
    key = os.getenv("NEWS_API_KEY", "")
    if not key:
        _set("News API", False, "Set NEWS_API_KEY environment variable (newsapi.org — free tier)")
        return
    try:
        import requests
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category": "technology", "pageSize": 1, "apiKey": key}, timeout=5
        )
        if r.status_code == 200:
            _set("News API", True, "NewsAPI connected")
        else:
            _set("News API", False, f"API error {r.status_code}")
    except Exception as e:
        _set("News API", False, f"Request failed: {e}")


# Master probe list — add new probes here to include in dashboard
_ALL_PROBES = [
    _probe_ollama,
    _probe_internet,
    _probe_microphone,
    _probe_screen_capture,
    _probe_webcam,
    _probe_filesystem,
    _probe_weather_api,
    _probe_spotify,
    _probe_calendar,
    _probe_contacts,
    _probe_tesseract,
    _probe_system_stats,
    _probe_news_api,
]


def run_all_probes():
    """Runs every probe once (blocking). Used on startup and for manual refresh."""
    for probe in _ALL_PROBES:
        try:
            probe()
        except Exception as e:
            logger.error(f"Probe {probe.__name__} raised uncaught exception: {e}")


def start_background_polling(interval_seconds: int = 5):
    """
    Starts a daemon thread that re-runs every probe every `interval_seconds`.
    Call once at startup from main.py.
    """
    def _loop():
        while True:
            run_all_probes()
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True, name="StatusPoller")
    t.start()
    logger.info(f"Status poller started (every {interval_seconds}s)")


# ─── PERMISSION GUIDE ─────────────────────────────────────────────────────────

PERMISSION_GUIDE = {
    "Microphone"    : "System Preferences → Security & Privacy → Privacy → Microphone → enable Terminal and JARVIS",
    "Camera"        : "System Preferences → Security & Privacy → Privacy → Camera → enable Terminal",
    "Screen Capture": "System Preferences → Security & Privacy → Privacy → Screen Recording → enable Terminal",
    "Accessibility" : "System Preferences → Security & Privacy → Privacy → Accessibility → enable Terminal",
    "Full Disk"     : "System Preferences → Security & Privacy → Privacy → Full Disk Access → enable Terminal",
    "Calendar"      : "System Preferences → Security & Privacy → Privacy → Calendars → enable JARVIS",
    "Contacts"      : "System Preferences → Security & Privacy → Privacy → Contacts → enable JARVIS",
    "Reminders"     : "System Preferences → Security & Privacy → Privacy → Reminders → enable JARVIS",
}


def fix_instructions(source_name: str) -> str:
    """Returns human-readable fix instructions for a given data source."""
    for perm, guide in PERMISSION_GUIDE.items():
        if perm.lower() in source_name.lower():
            return guide
    status = get(source_name)
    return status.get("message", "No specific fix instructions available.")


# ─── UNCERTAINTY RESPONSES ────────────────────────────────────────────────────

def honest_response(source_name: str, what_was_attempted: str) -> str:
    """
    Returns an honest, templated error message when a data source is unavailable.
    Used by every module before attempting real access — if offline, return this
    instead of making up data.
    """
    s = get(source_name)
    if s["ok"]:
        return ""   # source is available — proceed normally

    fix = fix_instructions(source_name)
    return (
        f"I cannot access {what_was_attempted} right now. "
        f"Reason: {s['message']}. "
        f"To fix this: {fix}"
    )
