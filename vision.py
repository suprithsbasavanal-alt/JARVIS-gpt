"""
vision.py
This file handles taking screenshots, reading text from the screen, and analyzing it.
"""
import pyautogui
import pytesseract
import cv2
import os
import logging
import brain # Import brain to analyze the text

logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def capture_and_read_screen():
    """
    Takes a screenshot, extracts text using OCR, and returns the text.
    """
    screenshot_path = "temp_screen.png"
    
    try:
        # Take a screenshot using PyAutoGUI
        print("Taking screenshot...")
        screenshot = pyautogui.screenshot()
        # Save it to a temporary file
        screenshot.save(screenshot_path)
        
        # Open the image using OpenCV for processing
        img = cv2.imread(screenshot_path)
        
        # Convert image to grayscale (helps OCR accuracy)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Use Tesseract to find text in the image
        print("Reading text from screenshot...")
        text = pytesseract.image_to_string(gray)
        
        # Delete the temporary file to save space
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            
        return text.strip()
        
    except Exception as e:
        error_msg = f"Error reading screen: {e}. Make sure Tesseract is installed."
        print(error_msg)
        logging.error(error_msg)
        return ""

def explain_screen():
    """
    Reads the screen and asks the AI to summarize what is on it.
    """
    screen_text = capture_and_read_screen()
    
    if not screen_text:
        return "I couldn't read any text on the screen."
        
    # Ask the AI to explain the text
    prompt = f"Here is the text I just read from the user's screen. Please summarize what is happening or what they are looking at in 1-2 sentences: {screen_text}"
    response = brain.ask_ollama(prompt, memory_context="User asked to explain screen")
    return response

def explain_error():
    """
    Reads the screen looking specifically for error messages and explains them.
    """
    screen_text = capture_and_read_screen()
    
    if not screen_text:
        return "I couldn't read any text on the screen."
        
    # Ask the AI to find and explain the error
    prompt = f"Look at this text from my screen and find any error messages. Explain what the error means and how to fix it simply: {screen_text}"
    response = brain.ask_ollama(prompt, memory_context="User has an error on screen")
    return response
    
def check_for_vision_commands(command_text):
    """Checks if the user asked a screen-related command."""
    command_text = command_text.lower()
    
    if "read my screen" in command_text or "what is on my screen" in command_text:
        return explain_screen()
    elif "explain this error" in command_text:
        return explain_error()
        
    return None
