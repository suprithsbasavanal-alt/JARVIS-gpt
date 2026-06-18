import os
import subprocess
import logging
import platform

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self):
        logger.info("Initializing Text-to-Speech engine...")
        self.system = platform.system()

    def speak(self, text: str) -> bool:
        """
        Synthesize text and play it.
        On macOS, falls back to the native 'say' CLI command.
        """
        logger.info(f"Speaking: {text}")
        if self.system == "Darwin":
            try:
                # Run 'say' in the background to avoid blocking the main execution
                subprocess.Popen(["say", text])
                return True
            except Exception as e:
                logger.error(f"macOS 'say' failed: {e}")
        
        # Fallback for other systems or when say fails
        logger.info(f"[TTS PLAYBACK MOCK]: {text}")
        return False

    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        Synthesize text to an audio file (e.g. wav or mp3).
        """
        logger.info(f"Synthesizing text to file {output_path}: {text}")
        if self.system == "Darwin":
            try:
                subprocess.run(["say", "-o", output_path, "--data-format=LEI16@22050", text], check=True)
                return True
            except Exception as e:
                logger.error(f"macOS 'say' file synthesis failed: {e}")
        
        return False

text_to_speech = TextToSpeech()
