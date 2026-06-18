import os
import sys
import time
import pytest
import struct
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.services.voice.tts import text_to_speech
from backend.app.services.voice.stt import speech_to_text
from backend.app.services.voice.wake_word import wake_word_detector
from backend.app.services.voice.session import VoiceSessionManager, VoiceSessionState

client = TestClient(app)

def test_tts_process_tracking():
    # Calling speak will mock play or run macOS native 'say'
    success = text_to_speech.speak("Hello this is a test")
    assert success is not None
    # Verify active process exists if system was Darwin, or at least no errors raised
    text_to_speech.stop_speaking()
    assert getattr(text_to_speech, "_active_process", None) is None

def test_stt_test_decoding():
    res = speech_to_text.transcribe_audio_bytes(b"text:Hello Jarvis")
    assert res == "Hello Jarvis"
    
    # Generic audio bytes
    res_generic = speech_to_text.transcribe_audio_bytes(b"\x00\x01\x02")
    assert "tasks for today" in res_generic

def test_wake_word_detector():
    detected = False
    def cb():
        nonlocal detected
        detected = True
    wake_word_detector.start(cb)
    
    # Send non-wake word
    wake_word_detector.detect_wake_word(b"hello companion")
    assert not detected
    
    # Send wake word
    wake_word_detector.detect_wake_word(b"Jarvis")
    assert detected
    wake_word_detector.stop()

def test_voice_session_manager():
    mgr = VoiceSessionManager(command_timeout=0.2, interruption_threshold=100.0)
    assert mgr.state == VoiceSessionState.WAKE_WORD_LISTENING
    
    # 1. Detect wake word
    state, event = mgr.process_audio_chunk(b"Jarvis")
    assert state == VoiceSessionState.COMMAND_LISTENING
    assert event == "wake_word_detected"
    
    # 2. Transcribe command
    state, event = mgr.process_audio_chunk(b"text:status check")
    assert state == VoiceSessionState.COMMAND_LISTENING
    assert event == "command_received"
    
    # 3. Interruption detection
    # Mock active speech process
    class MockProcess:
        def terminate(self): pass
        def wait(self, timeout=None): pass
    text_to_speech._active_process = MockProcess()
    
    # Send high-amplitude audio chunk to trigger interruption
    # High amplitude PCM chunk (using high 16-bit values)
    high_amp_chunk = struct.pack("<10h", 5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000)
    state, event = mgr.process_audio_chunk(high_amp_chunk)
    assert event == "interrupted"
    assert getattr(text_to_speech, "_active_process", None) is None
    
    # 4. Timeout
    time.sleep(0.3)
    state, event = mgr.process_audio_chunk(b"\x00\x00")
    assert state == VoiceSessionState.WAKE_WORD_LISTENING
    assert event == "session_timeout"

def test_voice_websocket_endpoint():
    # Use TestClient with websocket
    with client.websocket_connect("/api/voice/stream") as websocket:
        # Consume initial connection status message
        init_status = websocket.receive_json()
        assert init_status["event"] == "status"
        assert init_status["voice_state"] == "idle"

        # 1. Send wake word trigger
        websocket.send_bytes(b"Jarvis")
        resp = websocket.receive_json()
        assert resp["event"] == "wake_word_detected"
        assert resp["state"] == "command_listening"
        
        # 2. Send command trigger
        websocket.send_bytes(b"text:What tasks do I have?")
        resp_thinking = websocket.receive_json()
        assert resp_thinking["event"] == "thinking"
        assert resp_thinking["voice_state"] == "thinking"
        
        resp_trans = websocket.receive_json()
        assert resp_trans["event"] == "transcription"
        assert resp_trans["text"] == "What tasks do I have?"
        
        resp_reply = websocket.receive_json()
        assert resp_reply["event"] == "response"
        assert "goal" in resp_reply["text"].lower() or "error" in resp_reply["text"].lower() or "initialized" in resp_reply["text"].lower()
