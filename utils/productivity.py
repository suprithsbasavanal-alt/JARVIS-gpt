"""
utils/productivity.py
Handles productivity features like Pomodoro timers and tasks.
"""
import time
import threading
from voice.speaker import speak

def start_pomodoro(minutes=25):
    """Starts a Pomodoro timer in the background."""
    def timer_thread():
        print(f"Pomodoro started for {minutes} minutes.")
        time.sleep(minutes * 60)
        speak(f"Sir, your {minutes} minute pomodoro session is complete. Time for a break.")
        
    t = threading.Thread(target=timer_thread, daemon=True)
    t.start()
    return f"Starting a {minutes} minute focus timer."
