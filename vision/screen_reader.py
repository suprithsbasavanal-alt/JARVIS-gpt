"""
vision/screen_reader.py
Uses PyAutoGUI and Tesseract OCR to read text directly from the user's screen.
"""
import pyautogui
import pytesseract
import cv2
import os

def read_screen_text():
    """Takes a screenshot, performs OCR, and returns the extracted text."""
    temp_img = "temp_vision.png"
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(temp_img)
        
        # Open with OpenCV to process for better OCR accuracy
        img = cv2.imread(temp_img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Run Tesseract OCR
        text = pytesseract.image_to_string(gray)
        
        # Cleanup temp image
        if os.path.exists(temp_img):
            os.remove(temp_img)
            
        return text.strip()
    except Exception as e:
        print(f"Vision Error: {e}")
        return None
