"""
vision/face_auth.py
Basic face detection using OpenCV and the built-in Mac webcam.
"""
import cv2

def detect_face():
    """
    Captures a frame from the webcam and checks if a face is present.
    Uses basic Haar Cascades for speed and beginner-friendliness.
    """
    try:
        # Load the pre-trained face detection model from OpenCV
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Open the default webcam (0 is usually the built-in Mac camera)
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return "Could not access the webcam."
            
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return "Failed to capture image from webcam."
            
        # Convert image to grayscale for the cascade classifier
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        
        if len(faces) > 0:
            return f"I see {len(faces)} person(s) in front of the computer."
        else:
            return "I don't see anyone at the moment."
            
    except Exception as e:
        print(f"Camera Error: {e}")
        return "An error occurred while accessing the camera."
