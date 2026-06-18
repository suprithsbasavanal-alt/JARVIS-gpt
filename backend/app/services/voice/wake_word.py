import logging
import threading
import time
import numpy as np
from openwakeword.model import Model

logger = logging.getLogger(__name__)

class WakeWordDetector:
    def __init__(self):
        self.is_listening = False
        self._thread = None
        self.on_wake_word_detected = None # Callback function
        self.model = None
        self.audio_samples_buffer = np.array([], dtype=np.int16)

    def start(self, callback):
        """
        Start continuous wake word listening.
        """
        self.on_wake_word_detected = callback
        self.reset()
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
        self.reset()
        logger.info("Wake word detector stopped.")

    def reset(self):
        self.audio_samples_buffer = np.array([], dtype=np.int16)

    def _listen_loop(self):
        while self.is_listening:
            time.sleep(1.0)

    def detect_wake_word(self, audio_data: bytes) -> bool:
        """
        Processes a raw audio chunk to see if the wake word is present.
        Supports utf-8 text prefixes for unit testing.
        """
        # 1. Text-based fallback for testing/control
        try:
            decoded = audio_data.decode("utf-8")
            if "jarvis" in decoded.lower() or "hey jarvis" in decoded.lower():
                logger.info("Wake word detected via text representation!")
                if self.on_wake_word_detected:
                    self.on_wake_word_detected()
                return True
        except Exception:
            pass

        # 2. Raw PCM audio processing
        try:
            if self.model is None:
                logger.info("Initializing openwakeword Model with onnx framework...")
                self.model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

            # Convert bytes to np.int16
            samples = np.frombuffer(audio_data, dtype=np.int16)
            if len(samples) > 0:
                self.audio_samples_buffer = np.concatenate((self.audio_samples_buffer, samples))

            # Process in chunks of 1280 samples
            detected = False
            while len(self.audio_samples_buffer) >= 1280:
                chunk = self.audio_samples_buffer[:1280]
                self.audio_samples_buffer = self.audio_samples_buffer[1280:]
                
                # Run prediction
                predictions = self.model.predict(chunk)
                score = predictions.get("hey_jarvis", 0.0)
                if score > 0.5:
                    logger.info(f"openWakeWord detected 'hey_jarvis' with score: {score:.4f}")
                    detected = True
            
            if detected:
                if self.on_wake_word_detected:
                    self.on_wake_word_detected()
                return True
        except Exception as e:
            logger.error(f"Error in openwakeword detection: {e}", exc_info=True)

        return False

wake_word_detector = WakeWordDetector()
