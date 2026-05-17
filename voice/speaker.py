"""
voice/speaker.py
Handles Text-to-Speech (TTS) functionality.
"""
import pyttsx3

def speak(text, rate=175):
    """
    Converts text to spoken audio.
    Args:
        text (str): The text to speak.
        rate (int): The speed of speech.
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        
        # On Mac, 'Daniel' is a popular UK English male voice that sounds professional
        voices = engine.getProperty('voices')
        for voice in voices:
            if "Daniel" in voice.name:
                engine.setProperty('voice', voice.id)
                break
                
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")

def play_sound():
    """Plays a simple system sound for feedback (e.g. when waking up)."""
    import sys
    sys.stdout.write('\a')
    sys.stdout.flush()
