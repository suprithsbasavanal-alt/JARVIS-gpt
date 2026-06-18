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
    def __init__(self, command_timeout: float = 6.0, interruption_threshold: float = 1500.0, speech_threshold: float = 350.0, silence_timeout: float = 1.5):
        self.state = VoiceSessionState.WAKE_WORD_LISTENING
        self.command_timeout = command_timeout
        self.interruption_threshold = interruption_threshold
        self.speech_threshold = speech_threshold
        self.silence_timeout = silence_timeout
        self.last_activity_time = time.time()
        self.audio_buffer = bytearray()
        self.speech_started = False
        self.last_speech_time = None
        
    def process_audio_chunk(self, chunk: bytes) -> tuple[str, str | None]:
        """
        Processes an incoming raw PCM audio chunk.
        Returns a tuple of (current_state, event_triggered)
        """
        now = time.time()
        
        # 1. Check for active TTS (verifying subprocess is still running)
        active_proc = getattr(text_to_speech, "_active_process", None)
        is_tts_active = active_proc is not None and (active_proc.poll() is None if hasattr(active_proc, "poll") else True)
        
        # If JARVIS is speaking, prevent session timeout
        if is_tts_active:
            self.last_activity_time = now

        # 2. Check for command listening timeout
        if self.state == VoiceSessionState.COMMAND_LISTENING:
            if now - self.last_activity_time > self.command_timeout:
                logger.info("Command listening session timed out. Returning to wake word listening.")
                self.state = VoiceSessionState.WAKE_WORD_LISTENING
                self.speech_started = False
                self.last_speech_time = None
                return self.state, "session_timeout"

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

        # Calculate RMS amplitude of the chunk to detect speaking activity
        rms = 0.0 if is_test_command else self._calculate_rms(chunk)
            
        # 3. Check for User Interruption while JARVIS is speaking
        if is_tts_active and (rms > self.interruption_threshold or test_interrupt):
            logger.info(f"User interrupted JARVIS speech. Interruption RMS: {rms:.2f}")
            text_to_speech.stop_speaking()
            self.state = VoiceSessionState.COMMAND_LISTENING
            self.last_activity_time = now
            self.speech_started = True
            self.last_speech_time = now
            self.audio_buffer.clear()
            return self.state, "interrupted"

        # 4. Process according to current state
        if self.state == VoiceSessionState.WAKE_WORD_LISTENING:
            # Check for wake word
            if wake_word_detector.detect_wake_word(chunk):
                logger.info("Wake word detected! Entering command listening mode.")
                self.state = VoiceSessionState.COMMAND_LISTENING
                self.last_activity_time = now
                self.speech_started = False
                self.last_speech_time = None
                self.audio_buffer.clear()
                # Respond with wake acknowledgement
                text_to_speech.speak("Yes?")
                return self.state, "wake_word_detected"
        else:
            # We are in COMMAND_LISTENING state
            self.audio_buffer.extend(chunk)
            
            # Support text command triggers for testing
            try:
                decoded = chunk.decode("utf-8")
                if decoded.startswith("text:"):
                    self.last_activity_time = now
                    self.speech_started = False
                    self.last_speech_time = None
                    return self.state, "command_received"
            except Exception:
                pass
            
            # Continuous VAD (Voice Activity Detection) logic
            if not is_test_command:
                if rms > self.speech_threshold:
                    if not self.speech_started:
                        logger.info(f"VAD: Speech started detected (RMS: {rms:.2f})")
                        self.speech_started = True
                    self.last_speech_time = now
                    self.last_activity_time = now
                else:
                    if self.speech_started:
                        silence_duration = now - self.last_speech_time
                        # Prevent timeout while user is speaking/pausing but silence timeout not reached
                        self.last_activity_time = now
                        if silence_duration > self.silence_timeout:
                            logger.info(f"VAD: Silence detected for {silence_duration:.2f}s. Triggering transcription.")
                            self.speech_started = False
                            self.last_speech_time = None
                            return self.state, "command_received"
                
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
