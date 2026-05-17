"""
main.py
This is the entry point for the JARVIS application. Run this file to start the assistant.
"""
import sys
import threading
import json
import os
import logging
import time

# Import all our custom modules
import voice
import brain
import memory
import control
import automation
import vision
from ui import JarvisUI

# Import PyQt6 for the main application loop
from PyQt6.QtWidgets import QApplication

# Set up logging for the main file
logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to hold our UI instance
jarvis_ui = None

def load_config():
    """Loads the configuration from config.json or creates a default one."""
    default_config = {
        "name": "",
        "ai_model": "llama3",
        "wake_word_sensitivity": 0.5,
        "voice_speed": 175,
        "default_automation_modes": ["study", "coding", "movie", "sleep"]
    }
    
    config_file = "config.json"
    if not os.path.exists(config_file):
        # Create a new config file if it doesn't exist
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    else:
        # Load the existing config file
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return default_config

def save_config(config):
    """Saves the configuration to config.json"""
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

def process_command(text, config):
    """
    Takes the text spoken by the user and decides what to do with it.
    """
    try:
        # 1. Update UI with user's text
        if jarvis_ui:
            jarvis_ui.update_user_text_signal.emit(text)
            
        # 2. Check if it's a memory command (e.g., "remember my name is Arjun")
        if "remember" in text and "is" in text:
            # Simple extraction: "remember [key] is [value]"
            parts = text.split("remember ")[1].split(" is ")
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                memory.save_memory(key, value)
                response = f"Got it. I will remember that your {key} is {value}."
                
                # Update UI and Speak
                if jarvis_ui:
                    jarvis_ui.update_ai_text_signal.emit(response)
                voice.speak(response, speed=config['voice_speed'])
                return
                
        # 3. Check for Mac control commands (open apps, volume, etc.)
        control_response = control.execute_mac_command(text)
        if control_response:
            if jarvis_ui:
                jarvis_ui.update_ai_text_signal.emit(control_response)
            voice.speak(control_response, speed=config['voice_speed'])
            return
            
        # 4. Check for Automation Modes
        mode_response = automation.check_for_modes(text)
        if mode_response:
            if jarvis_ui:
                jarvis_ui.update_ai_text_signal.emit(mode_response)
            voice.speak(mode_response, speed=config['voice_speed'])
            return
            
        # 5. Check for Vision/Screen commands
        vision_response = vision.check_for_vision_commands(text)
        if vision_response:
            if jarvis_ui:
                jarvis_ui.update_ai_text_signal.emit(vision_response)
            voice.speak(vision_response, speed=config['voice_speed'])
            return
            
        # 6. If it's none of the above, send it to the AI brain
        if jarvis_ui:
            jarvis_ui.update_ai_text_signal.emit("Thinking...")
        
        # Get all memories to give context to the AI
        memory_context = memory.get_all_memories()
        # Get the AI's response
        ai_response = brain.ask_ollama(text, memory_context, config['ai_model'])
        
        # Update UI and Speak
        if jarvis_ui:
            jarvis_ui.update_ai_text_signal.emit(ai_response)
        voice.speak(ai_response, speed=config['voice_speed'])
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error while processing your command."
        logging.error(f"Error in process_command: {e}")
        if jarvis_ui:
            jarvis_ui.update_ai_text_signal.emit(error_msg)
        voice.speak(error_msg, speed=config['voice_speed'])

def jarvis_background_loop():
    """
    This function runs continuously in the background, waiting for the wake word.
    """
    config = load_config()
    
    # Initialize the memory database
    memory.setup_database()
    
    # First run check
    if not config.get('name'):
        ask_name_msg = "Hello. It looks like this is my first time running. What should I call you?"
        print(ask_name_msg)
        if jarvis_ui:
            jarvis_ui.update_ai_text_signal.emit(ask_name_msg)
        voice.speak(ask_name_msg, speed=config['voice_speed'])
        
        name_reply = voice.listen()
        if name_reply:
            config['name'] = name_reply
            save_config(config)
            memory.save_memory('name', name_reply)
            voice.speak(f"Thank you. I will call you {name_reply} from now on.", speed=config['voice_speed'])
        else:
            config['name'] = "Sir"
            save_config(config)
            voice.speak("I didn't catch that, I will call you Sir.", speed=config['voice_speed'])
    
    # Welcome message
    welcome_msg = f"Welcome online, {config['name']}. Systems are ready."
    print(welcome_msg)
    if jarvis_ui:
        jarvis_ui.update_ai_text_signal.emit(welcome_msg)
    voice.speak(welcome_msg, speed=config['voice_speed'])
    
    # Setup Wake Word with Picovoice Porcupine
    try:
        import pvporcupine
        import struct
        import pyaudio
        
        # IMPORTANT: Replace this with your Picovoice AccessKey
        ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY_HERE" 
        
        if ACCESS_KEY == "YOUR_PICOVOICE_ACCESS_KEY_HERE":
            raise ValueError("Please replace YOUR_PICOVOICE_ACCESS_KEY_HERE in main.py with your real key.")
            
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=['jarvis'],
            sensitivities=[config['wake_word_sensitivity']]
        )
        
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print("Listening for wake word 'Jarvis'...")
        while True:
            if jarvis_ui:
                jarvis_ui.update_ai_text_signal.emit("Waiting for 'Jarvis'...")
                
            # Read audio data from microphone
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            # Check if the wake word was detected
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                print("Wake word detected!")
                voice.play_beep()
                
                if jarvis_ui:
                    jarvis_ui.update_ai_text_signal.emit("Listening to command...")
                    
                # Listen for the actual command using SpeechRecognition
                command = voice.listen()
                
                if command:
                    # Process the command
                    process_command(command, config)
                else:
                    if jarvis_ui:
                        jarvis_ui.update_ai_text_signal.emit("I didn't hear a command.")
                
            time.sleep(0.01) # Small sleep to prevent maxing out CPU

    except Exception as e:
        error_msg = f"Wake word setup failed: {e}"
        print(error_msg)
        logging.error(error_msg)
        if jarvis_ui:
            jarvis_ui.update_ai_text_signal.emit(f"Error: {e}")
        # Fallback to normal listening if porcupine fails
        voice.speak("Wake word module failed. Please check the logs.", speed=config['voice_speed'])

def main():
    """The main function that starts the GUI and the background logic."""
    global jarvis_ui
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create and show the UI
    jarvis_ui = JarvisUI()
    jarvis_ui.show()
    
    # Start the Jarvis logic in a separate background thread
    # This prevents the GUI from freezing while Jarvis is listening or thinking
    background_thread = threading.Thread(target=jarvis_background_loop, daemon=True)
    background_thread.start()
    
    # Run the Qt application loop (this blocks until the window is closed)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
