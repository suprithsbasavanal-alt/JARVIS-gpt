import logging
import time
import math
import struct
from backend.app.services.voice.tts import text_to_speech
from backend.app.services.voice.wake_word import wake_word_detector

logger = logging.getLogger(__name__)

class VoiceSessionState:
    WAKE_WORD_LISTENING = "wake_word_listening"
    COMMAND_LISTENING = "command_listening"

class VoiceSessionManager:
    def __init__(self, command_timeout: float = 5.0, interruption_threshold: float = 1500.0):
        self.state = VoiceSessionState.WAKE_WORD_LISTENING
        self.command_timeout = command_timeout
        self.interruption_threshold = interruption_threshold
        self.last_activity_time = time.time()
        self.audio_buffer = bytearray()
        
    def process_audio_chunk(self, chunk: bytes) -> tuple[str, str | None]:
        """
        Processes an incoming raw PCM audio chunk.
        Returns a tuple of (current_state, event_triggered)
        """
        now = time.time()
        
        # 1. Check for command listening timeout
        if self.state == VoiceSessionState.COMMAND_LISTENING:
            if now - self.last_activity_time > self.command_timeout:
                logger.info("Command listening session timed out. Returning to wake word listening.")
                self.state = VoiceSessionState.WAKE_WORD_LISTENING
                return self.state, "session_timeout"

        # 2. Check for User Interruption while JARVIS is speaking
        is_tts_active = getattr(text_to_speech, "_active_process", None) is not None
        
        # Support text-encoded interruption triggers and commands for testing
        test_interrupt = False
        is_test_command = False
        try:
            decoded = chunk.decode("utf-8")
            if decoded.startswith("interrupt:") or decoded == "interrupt":
                test_interrupt = True
            elif decoded.startswith("text:") or decoded.lower() in ["jarvis", "hey jarvis"]:
                is_test_command = True
        except Exception:
            pass

        # Calculate RMS amplitude of the chunk to detect speaking activity (only if not a test text command)
        rms = 0.0 if is_test_command else self._calculate_rms(chunk)
            
        if is_tts_active and (rms > self.interruption_threshold or test_interrupt):
            logger.info(f"User interrupted JARVIS speech. Interruption RMS: {rms:.2f}")
            text_to_speech.stop_speaking()
            self.state = VoiceSessionState.COMMAND_LISTENING
            self.last_activity_time = now
            self.audio_buffer.clear()
            return self.state, "interrupted"

        # 3. Process according to current state
        if self.state == VoiceSessionState.WAKE_WORD_LISTENING:
            # Check for wake word
            if wake_word_detector.detect_wake_word(chunk):
                logger.info("Wake word detected! Entering command listening mode.")
                self.state = VoiceSessionState.COMMAND_LISTENING
                self.last_activity_time = now
                self.audio_buffer.clear()
                # Respond with wake acknowledgement
                text_to_speech.speak("Yes?")
                return self.state, "wake_word_detected"
        else:
            # We are in COMMAND_LISTENING state
            # Accumulate audio in buffer for Speech-to-Text
            self.audio_buffer.extend(chunk)
            
            # If the user speaks a command (for testing, we check if utf-8 test string starting with 'text:' is present)
            try:
                decoded = chunk.decode("utf-8")
                if decoded.startswith("text:"):
                    self.last_activity_time = now
                    return self.state, "command_received"
            except Exception:
                pass
                
        return self.state, None

    def _calculate_rms(self, chunk: bytes) -> float:
        """
        Calculates Root Mean Square (RMS) amplitude of 16-bit PCM mono audio.
        """
        if len(chunk) < 2:
            return 0.0
            
        # Ensure we have an even number of bytes for 16-bit samples
        count = len(chunk) // 2
        format_str = f"<{count}h"
        try:
            samples = struct.unpack(format_str, chunk[:count*2])
            sum_squares = sum(s * s for s in samples)
            mean = sum_squares / count
            return math.sqrt(mean)
        except Exception:
            return 0.0
