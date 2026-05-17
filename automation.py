"""
automation.py
This file handles preset modes that run multiple actions at once.
"""
import control
import time
import logging
import memory

logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def run_mode(mode_name):
    """
    Executes a series of actions based on the requested mode.
    
    Args:
        mode_name (str): The name of the mode to run (e.g., 'study').
        
    Returns:
        str: A message indicating the mode has started.
    """
    mode_name = mode_name.lower()
    
    try:
        # Built-in modes
        if "study" in mode_name:
            control.open_app("Notes")
            control.open_website("https://youtube.com")
            control.open_app("Spotify")
            control.set_volume(40)
            return "Study mode activated, good luck."
            
        elif "coding" in mode_name:
            control.open_app("Visual Studio Code")
            control.open_app("Terminal")
            control.open_website("https://github.com")
            control.set_volume(30)
            return "Coding mode ready."
            
        elif "movie" in mode_name:
            control.open_app("VLC") # Or Apple TV
            control.set_volume(80)
            # Screen dimming requires complex tools, so we skip it to avoid crashing
            return "Enjoy your movie."
            
        elif "sleep" in mode_name:
            control.close_app("Google Chrome")
            control.close_app("Spotify")
            control.close_app("Visual Studio Code")
            control.set_volume(0)
            return "Goodnight, shutting everything down."
            
        # Check custom modes in memory
        custom_modes_str = memory.get_memory("custom_modes")
        if custom_modes_str:
            import json
            custom_modes = json.loads(custom_modes_str)
            for custom_mode, actions in custom_modes.items():
                if custom_mode in mode_name:
                    # Execute custom actions (simplified)
                    for action in actions:
                        control.execute_mac_command(action)
                    return f"Custom mode {custom_mode} activated."
            
        return f"I do not have a mode called {mode_name} programmed yet."
            
    except Exception as e:
        logging.error(f"Error running mode {mode_name}: {e}")
        return "Sorry, there was an error running the mode."

def create_custom_mode(command_text):
    """
    Creates a new custom mode from user command.
    Example: "create a new mode called morning routine open chrome and set volume to 50"
    """
    try:
        # Simple extraction
        if "called" in command_text:
            parts = command_text.split("called")
            mode_details = parts[1].strip()
            # This is a very simplified parsing for beginner project
            return "Custom mode creation is partially implemented. You can edit config.json to add more."
    except Exception as e:
        logging.error(f"Error creating custom mode: {e}")
    return "Failed to create custom mode."

def check_for_modes(command_text):
    """
    Checks if the user asked to activate a mode.
    """
    command_text = command_text.lower()
    
    if "create a new mode" in command_text:
        return create_custom_mode(command_text)
        
    if "mode" in command_text:
        if "study" in command_text:
            return run_mode("study")
        elif "coding" in command_text:
            return run_mode("coding")
        elif "movie" in command_text:
            return run_mode("movie")
        elif "sleep" in command_text:
            return run_mode("sleep")
            
        # Extract mode name
        words = command_text.split("mode")
        if len(words) > 0:
            return run_mode(words[0].strip())
            
    return None
