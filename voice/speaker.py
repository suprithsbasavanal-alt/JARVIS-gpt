"""
voice/speaker.py
Handles Text-to-Speech (TTS) functionality using macOS native 'say' command for maximum stability.
"""
import os
import sys

def speak(text, rate=175):
    """
    Converts text to spoken audio.
    Args:
        text (str): The text to speak.
        rate (int): The speed of speech.
    """
    try:
        # Use macOS native 'say' command to avoid pyttsx3/pyobjc bugs on new Python versions
        # Escaping quotes to prevent injection
        safe_text = str(text).replace('"', '\\"')
        os.system(f'say -r {rate} -v "Daniel" "{safe_text}"')
    except Exception as e:
        print(f"TTS Error: {e}")

def play_sound():
    """Plays a simple system sound for feedback (e.g. when waking up)."""
    sys.stdout.write('\a')
    sys.stdout.flush()
