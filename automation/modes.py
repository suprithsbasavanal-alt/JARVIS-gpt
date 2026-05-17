"""
automation/modes.py
Defines complex multi-step workflows.
"""
import system.mac_control as mac
import utils.productivity as prod

def activate_mode(mode_name):
    """Activates a specific automation mode based on name."""
    mode_name = mode_name.lower()
    
    if "study" in mode_name:
        mac.open_app("Notes")
        mac.open_website("https://youtube.com/results?search_query=lofi+hip+hop+radio")
        mac.set_volume(30)
        prod.start_pomodoro(25)
        return "Study mode activated. Notes open, lo-fi music ready, and a 25-minute timer has started."
        
    elif "coding" in mode_name or "code" in mode_name:
        mac.open_app("Visual Studio Code")
        mac.open_app("Terminal")
        mac.open_website("https://github.com")
        mac.open_app("Spotify")
        mac.set_volume(40)
        return "Coding mode activated. VS Code, Terminal, and GitHub are ready."
        
    elif "movie" in mode_name:
        mac.open_app("VLC") # Default media player
        mac.set_volume(80)
        return "Movie mode activated. Enjoy the film, Sir."
        
    else:
        return f"I do not have a pre-configured workflow for {mode_name}."
