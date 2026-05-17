"""
system/mac_control.py
Handles interactions with macOS: opening apps, changing volume, locking screen, etc.
"""
import os
import subprocess

def open_app(app_name):
    """Opens a Mac app by name."""
    try:
        os.system(f"open -a '{app_name}'")
        return f"Opening {app_name}."
    except Exception:
        return f"Could not open {app_name}."

def close_app(app_name):
    """Closes a Mac app using AppleScript."""
    try:
        script = f'tell application "{app_name}" to quit'
        subprocess.run(['osascript', '-e', script])
        return f"Closed {app_name}."
    except Exception:
        return f"Could not close {app_name}."

def open_website(url):
    """Opens a website in Chrome (or default browser)."""
    try:
        os.system(f"open '{url}'")
        return "Opening website."
    except Exception:
        return "Failed to open website."

def set_volume(level):
    """Sets system volume (0-100)."""
    try:
        script = f'set volume output volume {level}'
        subprocess.run(['osascript', '-e', script])
        return f"Volume set to {level}%."
    except Exception:
        return "Failed to change volume."

def lock_screen():
    """Locks the Mac screen."""
    os.system("pmset displaysleepnow")
    return "Screen locked."

def shutdown_mac():
    """Initiates Mac shutdown."""
    subprocess.run(['osascript', '-e', 'tell app "System Events" to shut down'])
    return "Shutting down Mac."
