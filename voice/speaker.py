"""
voice/speaker.py  —  JARVIS 3.0 ULTIMATE
UPGRADE v3.0:
- Primary: macOS native 'say' with Daniel voice (zero dependency)
- Optional: ElevenLabs API for ultra-realistic voice
- Emotion-aware speed/pitch adjustment
- Async non-blocking speech via subprocess
- Cache frequently spoken phrases to avoid regenerating
- play_sound() uses afplay for reliable audio
"""

import os
import subprocess
import logging
import hashlib
import tempfile
import threading

logger = logging.getLogger("JARVIS.speaker")

# ── ElevenLabs config (optional — leave blank to use macOS say) ──────────────
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # default Rachel

# ── Audio cache directory ─────────────────────────────────────────────────────
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "sounds", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── Emotion → speech-rate adjustment (wpm offset) ────────────────────────────
_EMOTION_RATE = {
    "happy":       185,
    "excited":     200,
    "serious":     160,
    "calm":        155,
    "concerned":   165,
    "dramatic":    145,
    "whispering":  140,
    "motivational":180,
    "default":     172,
}


def _detect_emotion(text: str) -> str:
    """
    Very lightweight emotion heuristic based on keywords.
    Returns one of the keys in _EMOTION_RATE.
    """
    lower = text.lower()
    if any(w in lower for w in ["error", "failed", "warning", "cannot", "unable"]):
        return "concerned"
    if any(w in lower for w in ["completed", "success", "done", "ready", "great"]):
        return "happy"
    if any(w in lower for w in ["shutting", "goodbye", "sleep"]):
        return "calm"
    if any(w in lower for w in ["caution", "shutdown", "delete", "danger"]):
        return "serious"
    return "default"


def _speak_macos(text: str, rate: int):
    """Uses macOS built-in 'say' command. Blocks until speech finishes."""
    safe = text.replace('"', '\\"')
    # Daniel is a high-quality British English voice included with macOS
    cmd = f'say -r {rate} -v "Daniel" "{safe}"'
    try:
        subprocess.run(cmd, shell=True, check=False)
    except Exception as e:
        logger.error(f"macOS TTS error: {e}")


def _speak_elevenlabs(text: str) -> bool:
    """
    Uses ElevenLabs REST API to generate speech and plays it with afplay.
    Returns True on success, False on failure.
    """
    if not ELEVENLABS_API_KEY:
        return False
    try:
        import requests
        # Build cache key from text hash
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.mp3")

        # Serve from cache if available
        if os.path.exists(cache_path):
            subprocess.run(["afplay", cache_path], check=False)
            return True

        # Generate via ElevenLabs API
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.6, "similarity_boost": 0.85},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            with open(cache_path, "wb") as f:
                f.write(r.content)
            subprocess.run(["afplay", cache_path], check=False)
            return True
        logger.warning(f"ElevenLabs API returned {r.status_code}")
        return False
    except Exception as e:
        logger.error(f"ElevenLabs error: {e}")
        return False


def speak(text: str, emotion: str = "auto", block: bool = True):
    """
    Converts text to speech.

    Args:
        text:    The string to speak.
        emotion: One of the _EMOTION_RATE keys, or 'auto' to detect from text.
        block:   If False, speech runs in a daemon thread (non-blocking).
    """
    if not text or not text.strip():
        return

    if emotion == "auto":
        emotion = _detect_emotion(text)

    rate = _EMOTION_RATE.get(emotion, _EMOTION_RATE["default"])
    logger.info(f"Speaking [{emotion}@{rate}wpm]: {text[:60]}…")

    def _do_speak():
        # Try ElevenLabs first; fall back to macOS say
        if not _speak_elevenlabs(text):
            _speak_macos(text, rate)

    if block:
        _do_speak()
    else:
        t = threading.Thread(target=_do_speak, daemon=True)
        t.start()


def play_sound(sound_name: str = "activate"):
    """
    Plays a short sound effect from the sounds/ directory.
    Falls back to a system bell if the file is not found.

    Args:
        sound_name: 'activate' | 'error' | 'complete' | 'notification'
    """
    sounds_dir = os.path.join(os.path.dirname(__file__), "..", "sounds")
    path = os.path.join(sounds_dir, f"{sound_name}.wav")
    if os.path.exists(path):
        try:
            subprocess.Popen(["afplay", path])   # non-blocking
        except Exception as e:
            logger.error(f"afplay error: {e}")
    else:
        # Fallback: macOS system bell via osascript
        os.system('osascript -e "beep"')
