import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, Conversation, Message
from backend.app.services.voice.session import VoiceSessionManager, VoiceSessionState
from backend.app.services.voice.stt import speech_to_text
from backend.app.services.voice.tts import text_to_speech
from backend.app.services.executive.router import CognitiveRouter
from backend.app.agents.planner import PlannerAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice Presence System"])

planner = PlannerAgent()

@router.websocket("/stream")
async def websocket_voice_stream(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket channel for streaming raw PCM audio. Handles wake-word detection,
    STT transcription, continuous conversational logic, and user interruptions.
    """
    await websocket.accept()
    logger.info("Voice stream WebSocket connected.")
    
    session_manager = VoiceSessionManager(command_timeout=6.0, interruption_threshold=1500.0)
    
    # Send initial connection state
    await websocket.send_json({
        "event": "status",
        "state": session_manager.state,
        "voice_state": "idle",
        "text": "System ready. Say 'Hey Jarvis' to activate."
    })
    
    try:
        while True:
            # 1. Receive binary PCM chunk
            data = await websocket.receive_bytes()
            
            # 2. Process chunk through session manager
            state, event = session_manager.process_audio_chunk(data)
            
            # Determine current voice state
            voice_state = session_manager.get_voice_state() if hasattr(session_manager, "get_voice_state") else "idle"
            
            if event == "wake_word_detected":
                await websocket.send_json({
                    "event": "wake_word_detected",
                    "state": state,
                    "voice_state": "listening",
                    "text": "Yes?"
                })
                
            elif event == "interrupted":
                await websocket.send_json({
                    "event": "interrupted",
                    "state": state,
                    "voice_state": "listening",
                    "text": "Listening..."
                })
                
            elif event == "session_timeout":
                await websocket.send_json({
                    "event": "session_timeout",
                    "state": state,
                    "voice_state": "idle",
                    "text": "Standby."
                })
                
            elif event == "command_received" or (state == VoiceSessionState.COMMAND_LISTENING and len(session_manager.audio_buffer) >= 320000):
                # We have enough accumulated audio bytes or VAD silence threshold was met
                
                # Signal thinking state
                session_manager.is_thinking = True
                await websocket.send_json({
                    "event": "thinking",
                    "state": state,
                    "voice_state": "thinking",
                    "text": "Processing speech..."
                })
                
                raw_text = speech_to_text.transcribe_audio_bytes(bytes(session_manager.audio_buffer))
                session_manager.audio_buffer.clear()
                
                if raw_text and raw_text.strip():
                    await websocket.send_json({
                        "event": "transcription",
                        "state": state,
                        "voice_state": "thinking",
                        "text": raw_text
                    })
                    
                    # Process the query using Planner / Cognitive Routing
                    reply_content = ""
                    try:
                        # Pass DB session correctly
                        is_fast, fast_reply, _, _ = CognitiveRouter.evaluate_path(raw_text, db)
                        if is_fast and fast_reply:
                            reply_content = fast_reply
                        else:
                            # Use planner to reason
                            plan = planner.create_plan(raw_text, db)
                            reply_content = f"I have initialized the goal: '{plan['goal']}'. Processing subtasks."
                    except Exception as e:
                        logger.error(f"Error processing voice query: {e}", exc_info=True)
                        reply_content = f"I encountered an error processing your query: {e}"
                        
                    # Transition to speaking
                    session_manager.is_thinking = False
                    
                    # Speak response
                    text_to_speech.speak(reply_content)
                    
                    # Send response back to frontend HUD
                    await websocket.send_json({
                        "event": "response",
                        "state": state,
                        "voice_state": "speaking",
                        "text": reply_content
                    })
                    
                    # Reset activity timer
                    session_manager.last_activity_time = session_manager.last_activity_time
                else:
                    session_manager.is_thinking = False
                    await websocket.send_json({
                        "event": "empty_transcription",
                        "state": state,
                        "voice_state": "listening",
                        "text": "Listening..."
                    })
                    
    except WebSocketDisconnect:
        logger.info("Voice stream WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Voice stream WebSocket encountered error: {e}", exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        # Cleanup when socket closes
        text_to_speech.stop_speaking()
