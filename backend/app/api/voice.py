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
    
    try:
        while True:
            # 1. Receive binary PCM chunk
            data = await websocket.receive_bytes()
            
            # 2. Process chunk through session manager
            state, event = session_manager.process_audio_chunk(data)
            
            if event == "wake_word_detected":
                await websocket.send_json({
                    "event": "wake_word_detected",
                    "state": state,
                    "text": "Yes?"
                })
                
            elif event == "interrupted":
                await websocket.send_json({
                    "event": "interrupted",
                    "state": state,
                    "text": "Active response stopped. Listening for your instruction."
                })
                
            elif event == "session_timeout":
                await websocket.send_json({
                    "event": "session_timeout",
                    "state": state,
                    "text": "Listening session timed out. Re-arming wake word detector."
                })
                
            elif event == "command_received" or (state == VoiceSessionState.COMMAND_LISTENING and len(session_manager.audio_buffer) >= 32000):
                # We have enough accumulated audio bytes or a test trigger was decoded
                raw_text = speech_to_text.transcribe_audio_bytes(bytes(session_manager.audio_buffer))
                session_manager.audio_buffer.clear()
                
                if raw_text and raw_text.strip():
                    await websocket.send_json({
                        "event": "transcription",
                        "state": state,
                        "text": raw_text
                    })
                    
                    # Process the query using Planner / Cognitive Routing
                    reply_content = ""
                    try:
                        is_fast, fast_reply, _ = CognitiveRouter.evaluate_path(raw_text)
                        if is_fast:
                            reply_content = fast_reply
                        else:
                            # Use planner to reason or default to simple response
                            plan = planner.create_plan(raw_text, db)
                            # Get the first subtask or general planner comment
                            reply_content = f"I have initialized the goal: '{plan['goal']}'. Processing subtasks."
                    except Exception as e:
                        logger.error(f"Error processing voice query: {e}")
                        reply_content = f"I encountered an error processing your query: {e}"
                        
                    # Send response back to frontend HUD
                    await websocket.send_json({
                        "event": "response",
                        "state": state,
                        "text": reply_content
                    })
                    
                    # Speak response
                    text_to_speech.speak(reply_content)
                    
                    # Update activity timer
                    session_manager.last_activity_time = session_manager.last_activity_time
                    
    except WebSocketDisconnect:
        logger.info("Voice stream WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Voice stream WebSocket encountered error: {e}", exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass
