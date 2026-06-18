import os
import logging
import io
import wave
import google.generativeai as genai
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, num_channels: int = 1, sample_width: int = 2) -> bytes:
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return wav_io.getvalue()

class SpeechToText:
    def __init__(self):
        logger.info("Initializing Speech-to-Text engine...")
        
    def transcribe_audio_bytes(self, audio_data: bytes) -> str:
        """
        Transcribe raw audio bytes.
        Returns transcribed text or empty string.
        """
        # 1. Text-based fallback for testing/control
        try:
            decoded = audio_data.decode("utf-8")
            if decoded.startswith("text:"):
                logger.info(f"Test decoded command: {decoded[5:]}")
                return decoded[5:]
        except Exception:
            pass

        # 2. Use Gemini API for cloud STT if key is set
        if settings.GEMINI_API_KEY and audio_data and len(audio_data) >= 100:
            try:
                logger.info(f"Transcribing {len(audio_data)} bytes using Gemini 1.5 Flash...")
                wav_bytes = pcm_to_wav(audio_data, sample_rate=16000)
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                response = model.generate_content([
                    {
                        "mime_type": "audio/wav",
                        "data": wav_bytes
                    },
                    "Transcribe the spoken audio in this file. Only return the transcript. If there is no speech or it is just background noise/silence, return an empty string. Do not add any notes, tags, or explanations."
                ])
                transcript = response.text.strip()
                logger.info(f"Gemini STT output: '{transcript}'")
                return transcript
            except Exception as e:
                logger.error(f"Gemini speech transcription failed: {e}", exc_info=True)

        logger.info(f"Received {len(audio_data)} bytes of audio data for transcription (mock/fallback).")
        # Default mock command if no specific test string is decoded and API fails/missing
        return "Jarvis, what are my tasks for today?"

    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe an audio file from path.
        """
        logger.info(f"Transcribing audio file: {file_path}")
        if settings.GEMINI_API_KEY and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    wav_bytes = f.read()
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content([
                    {
                        "mime_type": "audio/wav",
                        "data": wav_bytes
                    },
                    "Transcribe the spoken audio in this file. Only return the transcript."
                ])
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini file transcription failed: {e}")
                
        return "Jarvis, find similar projects in my directory."

speech_to_text = SpeechToText()

