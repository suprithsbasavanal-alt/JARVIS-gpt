"""
voice/listener.py
Handles Speech-to-Text and Wake Word detection using PyAudio and Porcupine.
"""
import speech_recognition as sr
import pvporcupine
import pyaudio
import struct

# IMPORTANT: You must add your Picovoice Access Key here to use the wake word
PICOVOICE_API_KEY = "YOUR_PICOVOICE_ACCESS_KEY_HERE"

def listen_for_command():
    """
    Listens to the microphone and converts speech to text.
    Returns the recognized text as a string.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        # Adjust for ambient noise for better accuracy
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            text = recognizer.recognize_google(audio)
            print(f"User: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("Network error with speech recognition.")
            return ""
        except Exception as e:
            print(f"Microphone error: {e}")
            return ""

def wait_for_wake_word(callback_on_wake):
    """
    Continuously listens for the 'Jarvis' wake word using Porcupine.
    When detected, it calls the provided callback function.
    """
    if PICOVOICE_API_KEY == "YOUR_PICOVOICE_ACCESS_KEY_HERE":
        print("WARNING: Picovoice Access Key not set. Please get one from console.picovoice.ai")
        # Beginner fallback: If no key, just use normal speech recognition in a loop
        import time
        while True:
            text = listen_for_command()
            if "jarvis" in text:
                command = text.split("jarvis", 1)[-1].strip()
                callback_on_wake(command)
            time.sleep(0.5)
        return
            
    try:
        # Initialize Porcupine with the default 'jarvis' keyword
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_API_KEY,
            keywords=['jarvis']
        )
        
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print("Wake Word Engine Started. Say 'Jarvis' to wake me up.")
        
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                callback_on_wake()
                
    except Exception as e:
        print(f"Wake word error: {e}")
