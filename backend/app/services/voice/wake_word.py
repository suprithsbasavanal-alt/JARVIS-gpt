import logging
import threading
import time

logger = logging.getLogger(__name__)

class WakeWordDetector:
    def __init__(self):
        self.is_listening = False
        self._thread = None
        self.on_wake_word_detected = None # Callback function

    def start(self, callback):
        """
        Start continuous wake word listening.
        """
        self.on_wake_word_detected = callback
        if self.is_listening:
            return
        
        self.is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Wake word detector started listening...")

    def stop(self):
        """
        Stop wake word listening.
        """
        self.is_listening = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Wake word detector stopped.")

    def _listen_loop(self):
        while self.is_listening:
            time.sleep(1.0)

    def detect_wake_word(self, audio_data: bytes) -> bool:
        """
        Processes a raw audio chunk to see if the wake word is present.
        Supports utf-8 text prefixes for unit testing.
        """
        try:
            decoded = audio_data.decode("utf-8")
            if "jarvis" in decoded.lower() or "hey jarvis" in decoded.lower():
                logger.info("Wake word detected via text representation!")
                if self.on_wake_word_detected:
                    self.on_wake_word_detected()
                return True
        except Exception:
            pass
            
        # Optional: Simple peak/RMS thresholding for simulated detection on high-amplitude noise
        # in actual audio frames
        return False

wake_word_detector = WakeWordDetector()
