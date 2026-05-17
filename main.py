"""
main.py
The central brain of JARVIS. This file coordinates all modules, starts the UI,
and runs the main background listening loop.
"""
import sys
import threading
import time

# Import our modular components
import memory.database as db
import voice.speaker as speaker
import voice.listener as listener
import brain.llm as llm
from agents.master_agent import master
import system.mac_control as mac
import automation.modes as modes
import vision.screen_reader as screen_reader
import vision.face_auth as face_auth
import utils.internet as internet
import utils.productivity as prod
import utils.file_system as fs
import memory.rag as rag
from ui.hud import CinematicHUD

from PyQt6.QtWidgets import QApplication

# Global reference to our UI
hud = None

def execute_command(command):
    """
    Parses the recognized voice command and executes the corresponding action.
    """
    global hud
    if hud:
        hud.sig_update_user.emit(command)
    
    command_lower = command.lower()
    response = ""

    try:
        # 1. System Control Commands
        if "open" in command_lower and "mode" not in command_lower:
            import re
            match = re.search(r'open\s+([a-zA-Z0-9\s]+?)(?=\s+and|\s*$)', command_lower)
            if match:
                app_name = match.group(1).strip()
                if app_name == "chrome":
                    response = mac.open_app("Google Chrome")
                elif app_name in ["vs code", "vscode"]:
                    response = mac.open_app("Visual Studio Code")
                else:
                    response = mac.open_app(app_name)
                
            # Check if there's a chained command like "and read the screen"
            if "and read the screen" in command_lower or "and read the" in command_lower:
                time.sleep(2)  # Wait for app to open
                screen_text = screen_reader.read_screen_text()
                if screen_text:
                    prompt = f"I am looking at my screen and it says: '{screen_text}'. Please summarize it briefly."
                    response += " " + llm.generate_response(prompt)
                
        elif "close" in command_lower:
            app_name = command_lower.replace("close", "").strip()
            response = mac.close_app(app_name)
            
        elif "shutdown mac" in command_lower:
            response = mac.shutdown_mac()
            
        elif "lock screen" in command_lower:
            response = mac.lock_screen()
            
        elif "volume" in command_lower:
            import re
            nums = re.findall(r'\d+', command_lower)
            if nums:
                response = mac.set_volume(nums[0])
            else:
                response = "Please specify a volume level."
                
        elif "turn on bluetooth" in command_lower:
            response = mac.toggle_bluetooth(True)
        elif "turn off bluetooth" in command_lower:
            response = mac.toggle_bluetooth(False)
        elif "turn on wi-fi" in command_lower or "turn on wifi" in command_lower:
            response = mac.toggle_wifi(True)
        elif "turn off wi-fi" in command_lower or "turn off wifi" in command_lower:
            response = mac.toggle_wifi(False)

        # 2. Automation Modes
        elif "start" in command_lower and "mode" in command_lower:
            response = modes.activate_mode(command_lower)

        # 3. Vision AI Features
        elif "read my screen" in command_lower or "what is on my screen" in command_lower:
            screen_text = screen_reader.read_screen_text()
            if screen_text:
                prompt = f"I am looking at my screen and it says: '{screen_text}'. Please summarize it briefly."
                response = llm.generate_response(prompt)
            else:
                response = "I couldn't detect any text on your screen."
                
        elif "explain this error" in command_lower:
            screen_text = screen_reader.read_screen_text()
            if screen_text:
                prompt = f"Find the error message in this text and explain how to fix it: '{screen_text}'"
                response = llm.generate_response(prompt)
            else:
                response = "I couldn't read any error on the screen."
            
        elif "who is in front of the computer" in command_lower or "look through webcam" in command_lower:
            response = face_auth.detect_face()

        # 4. Internet Features
        elif "weather" in command_lower:
            response = internet.get_weather()
            
        elif "search youtube for" in command_lower:
            query = command_lower.replace("search youtube for", "").strip()
            response = internet.search_youtube(query)
            
        elif "search google for" in command_lower:
            query = command_lower.replace("search google for", "").strip()
            response = internet.search_google(query)

        # 5. Memory & RAG System
        elif "deeply remember" in command_lower or "store in long term memory" in command_lower:
            # Add to RAG vector database
            text_to_save = command_lower.replace("deeply remember", "").replace("store in long term memory", "").strip()
            success = rag.add_document(text_to_save)
            response = "I have encoded that into my long-term semantic memory." if success else "I failed to encode that into memory."
            
        elif "remember" in command_lower:
            # SQLite key-value facts
            if " is " in command_lower:
                parts = command_lower.split(" is ")
                if len(parts) == 2:
                    key = parts[0].replace("remember", "").strip()
                    val = parts[1].strip()
                    db.save_fact(key, val)
                    response = f"I have saved that your {key} is {val}."
            elif "remember to" in command_lower:
                task = command_lower.replace("remember to", "").strip()
                db.add_task(task)
                response = f"I have added {task} to your task list."
            else:
                response = "I didn't quite catch the format. Try 'remember [item] is [value]'."

        # 6. File System Access
        elif "find file" in command_lower or "read file" in command_lower:
            filename = command_lower.replace("find file", "").replace("read file", "").strip()
            filepath = fs.find_file(filename)
            if filepath:
                content = fs.read_file_content(filepath)
                if "read" in command_lower:
                    prompt = f"Summarize the contents of this file: {content}"
                    response = llm.generate_response(prompt)
                else:
                    response = f"I found the file at {filepath}."
            else:
                response = f"I could not locate {filename} on your system."

        # 6. Default to AI Brain (Multi-Agent Router)
        else:
            if hud:
                hud.sig_update_ai.emit("Analyzing request...")
            response = master.process_request(command)

        # Output the response
        if response:
            if hud:
                hud.sig_update_ai.emit(response)
            speaker.speak(response)

    except Exception as e:
        print(f"Execution Error: {e}")
        err_msg = "Sorry Sir, I encountered an error executing that command."
        if hud:
            hud.sig_update_ai.emit(err_msg)
        speaker.speak(err_msg)

def jarvis_wake_routine(pre_command=""):
    """Called when the wake word is detected. Enters active conversation mode."""
    speaker.play_sound()
    
    # 1. Handle the initial command
    command = pre_command
    if not command:
        if hud:
            hud.sig_update_ai.emit("Listening...")
        command = listener.listen_for_command()

    # 2. Continuous Active Listening Loop
    while command:
        # Check for exit commands
        stop_words = ["stop", "exit", "standby", "nevermind", "that's all", "bye", "goodbye"]
        if any(word == command.strip() or f"{word} jarvis" == command.strip() for word in stop_words):
            if hud:
                hud.sig_update_ai.emit("Standing by.")
            speaker.speak("Standing by.")
            break
            
        # Execute the user's command
        execute_command(command)
        
        # After finishing the task and speaking, immediately listen again!
        if hud:
            hud.sig_update_ai.emit("Listening...")
        command = listener.listen_for_command()
        
    if hud:
        hud.sig_update_ai.emit("Awaiting wake word...")
        


def background_loop():
    """Runs continuously in the background."""
    # Initialize SQLite Database
    db.init_db()
    
    # Startup greeting
    name = db.get_fact("name") or "Sir"
    greeting = f"Welcome back, {name}. All systems are online and ready."
    print(greeting)
    
    # Give the UI a second to load completely
    time.sleep(1)
    
    if hud:
        hud.sig_update_ai.emit(greeting)
    speaker.speak(greeting)
    
    # Start wake word listener (this blocks the thread, which is fine since it's a background thread)
    listener.wait_for_wake_word(jarvis_wake_routine)

def main():
    """Starts the application."""
    global hud
    
    app = QApplication(sys.argv)
    
    # Initialize UI
    hud = CinematicHUD()
    hud.show()
    
    # Start background logic in a separate thread to prevent freezing the GUI
    bg_thread = threading.Thread(target=background_loop, daemon=True)
    bg_thread.start()
    
    # Run the GUI event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
