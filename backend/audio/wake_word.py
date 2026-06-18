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
        # Placeholder for openwakeword / audio stream listener loop
        while self.is_listening:
            # Sleep to prevent high CPU utilization in mock state
            time.sleep(1.0)
            # In a real setup, we would read audio frame from microphone or stream
            # and run it through openwakeword model.

wake_word_detector = WakeWordDetector()
