"""
voice.py
This file handles everything related to voice: listening to the microphone and speaking out loud.
"""
import speech_recognition as sr
import pyttsx3
import logging

# Set up logging to record errors
logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def speak(text, speed=175):
    """
    Converts text to speech so Jarvis can talk.
    
    Args:
        text (str): The text Jarvis should say.
        speed (int): The speed of the voice.
    """
    try:
        # Initialize the text-to-speech engine
        engine = pyttsx3.init()
        # Set the voice speed
        engine.setProperty('rate', speed)
        # Speak the text
        engine.say(text)
        # Wait for the speech to finish
        engine.runAndWait()
    except Exception as e:
        error_msg = f"Error in speak function: {e}"
        print(error_msg)
        logging.error(error_msg)

def listen():
    """
    Listens to the microphone and converts spoken words into text.
    
    Returns:
        str: The text that was spoken, or an empty string if it failed.
    """
    # Create a recognizer object
    recognizer = sr.Recognizer()
    
    try:
        # Use the default microphone as the audio source
        with sr.Microphone() as source:
            print("Listening for command...")
            # Adjust for background noise for better accuracy
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Listen to the audio
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Recognizing...")
            # Use Google's speech recognition to convert audio to text
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
            
    except sr.WaitTimeoutError:
        print("Listening timed out.")
        return ""
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return ""
    except sr.RequestError as e:
        error_msg = f"Could not request results from Google Speech API: {e}"
        print(error_msg)
        logging.error(error_msg)
        return ""
    except Exception as e:
        error_msg = f"Error in listen function: {e}"
        print(error_msg)
        logging.error(error_msg)
        return ""

def play_beep():
    """Plays a short beep sound to indicate Jarvis is awake."""
    try:
        import sys
        # Print a bell character which often triggers the system beep on Mac
        sys.stdout.write('\a')
        sys.stdout.flush()
    except Exception as e:
        logging.error(f"Error playing beep: {e}")
