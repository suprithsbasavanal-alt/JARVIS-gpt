"""
control.py
This file contains functions to control the Mac computer (open apps, change volume, etc.).
"""
import os
import subprocess
import logging

logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def open_app(app_name):
    """Opens a Mac application by its name."""
    try:
        # Use the macOS 'open' command to launch the app
        os.system(f"open -a '{app_name}'")
        return f"Opening {app_name}"
    except Exception as e:
        logging.error(f"Error opening app {app_name}: {e}")
        return f"Failed to open {app_name}"

def open_website(url):
    """Opens a website in Google Chrome."""
    try:
        # Open URL in Chrome
        os.system(f"open -a 'Google Chrome' '{url}'")
        return f"Opening website"
    except Exception as e:
        logging.error(f"Error opening website: {e}")
        return "Failed to open website"

def close_app(app_name):
    """Closes a Mac application by its name using AppleScript."""
    try:
        # Use AppleScript to quit the application gracefully
        script = f'tell application "{app_name}" to quit'
        subprocess.run(['osascript', '-e', script])
        return f"Closing {app_name}"
    except Exception as e:
        logging.error(f"Error closing app {app_name}: {e}")
        return f"Failed to close {app_name}"

def set_volume(percentage):
    """Sets the system volume to a specific percentage (0-100)."""
    try:
        # Use AppleScript to set volume
        script = f'set volume output volume {percentage}'
        subprocess.run(['osascript', '-e', script])
        return f"Volume set to {percentage} percent"
    except Exception as e:
        logging.error(f"Error setting volume: {e}")
        return "Failed to set volume"

def get_battery_percentage():
    """Gets the current battery percentage of the Mac."""
    try:
        # Run pmset command to get battery info
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        output = result.stdout
        # Extract the percentage from the text output
        import re
        match = re.search(r'(\d+)%', output)
        if match:
            return f"Battery is at {match.group(1)} percent."
        return "Could not determine battery percentage."
    except Exception as e:
        logging.error(f"Error getting battery: {e}")
        return "Failed to check battery."

def execute_mac_command(command_text):
    """
    Checks the user's spoken text for system commands and executes them.
    
    Args:
        command_text (str): The text spoken by the user.
        
    Returns:
        str or None: A response if a command was executed, otherwise None.
    """
    command_text = command_text.lower()
    
    try:
        # Check for various keywords in the command
        if "open chrome" in command_text:
            return open_app("Google Chrome")
        elif "open spotify" in command_text:
            return open_app("Spotify")
        elif "open vs code" in command_text or "open vscode" in command_text:
            return open_app("Visual Studio Code")
        elif "open terminal" in command_text:
            return open_app("Terminal")
        elif "open finder" in command_text:
            return open_app("Finder")
        elif "open notes" in command_text:
            return open_app("Notes")
        elif "open website" in command_text:
            return open_website("https://google.com") # Default to google
            
        elif "close" in command_text:
            # Extract the app name after the word "close"
            words = command_text.split("close")
            if len(words) > 1:
                app_name = words[1].strip()
                return close_app(app_name)
                
        elif "increase volume" in command_text:
            # Tell AppleScript to increase volume
            subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 10)'])
            return "Volume increased"
        elif "decrease volume" in command_text:
            subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 10)'])
            return "Volume decreased"
        elif "mute" in command_text and "unmute" not in command_text:
            subprocess.run(['osascript', '-e', 'set volume with output muted'])
            return "Muted"
        elif "unmute" in command_text:
            subprocess.run(['osascript', '-e', 'set volume without output muted'])
            return "Unmuted"
            
        elif "battery" in command_text:
            return get_battery_percentage()
            
        elif "screenshot" in command_text:
            # macOS default shortcut command for screenshot to file
            os.system("screencapture ~/Desktop/screenshot_jarvis.png")
            return "Screenshot saved to your Desktop."
            
        elif "lock screen" in command_text:
            # Command to lock the Mac screen
            os.system("pmset displaysleepnow")
            return "Locking screen."
            
        elif "shutdown mac" in command_text:
            # Shutdown Mac (might require password, so we just return a message or use AppleScript)
            subprocess.run(['osascript', '-e', 'tell app "System Events" to shut down'])
            return "Shutting down Mac."
            
        elif "restart mac" in command_text:
            subprocess.run(['osascript', '-e', 'tell app "System Events" to restart'])
            return "Restarting Mac."
            
        return None # No system command detected
        
    except Exception as e:
        logging.error(f"Error in execute_mac_command: {e}")
        return None
