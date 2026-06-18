import os
import uuid
import logging
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db, Conversation, Message, Task, Memory, AuditLog
from backend.app.agents.planner import PlannerAgent
from backend.app.agents.vision_agent import vision_agent
from backend.app.services.voice.tts import text_to_speech
from backend.app.services.voice.stt import speech_to_text

# Configure Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("jarvis_backend")

# Create database tables automatically
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="JARVIS AI Desktop Operating Assistant Backend",
    description="Python AI Core backend for task planning, voice integration, memory, and desktop control.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Agent
planner = PlannerAgent()

# Request schemas
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    assigned_agent: str | None = None

class SettingUpdate(BaseModel):
    key: str
    value: str

# Endpoints
@app.get("/")
def read_root():
    return {"status": "online", "message": "JARVIS Core API is running."}

@app.post("/api/chat/message")
def post_chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Primary endpoint for user text input. Triggers planner reasoning.
    """
    logger.info(f"Received message: {request.message} in conversation: {request.conversation_id}")
    
    # 1. Resolve or create conversation
    conv_id = request.conversation_id
    if not conv_id:
        conversation = Conversation(title=request.message[:50])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conv_id = str(conversation.id)
    else:
        conversation = db.query(Conversation).filter(Conversation.id == uuid.UUID(conv_id)).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Store User Message
    user_msg = Message(
        conversation_id=conversation.id,
        sender="user",
        content=request.message
    )
    db.add(user_msg)
    db.commit()

    # Check for simple greetings
    greetings = {"hi", "hello", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening", "jarvis"}
    clean_msg = request.message.strip().lower().replace("!", "").replace(".", "")
    if clean_msg in greetings:
        plan = {
            "goal": "Respond to greeting",
            "tasks": []
        }
        reply_content = "Hello! I am JARVIS, your AI Desktop Operating Assistant. I am running locally and ready to help. How can I assist you today?"
        text_to_speech.speak("Hello. I am online and ready.")
    else:
        # 3. Trigger Planner reasoning to create plan and subtasks
        plan = planner.create_plan(request.message, db)
        
        # 4. Execute planning/research steps
        research_task = next((t for t in plan["tasks"] if t["agent"] == "researcher"), None)
        
        if research_task:
            from backend.app.agents.researcher import ResearchAgent
            researcher = ResearchAgent()
            
            # Mark the task as in_progress in DB
            db_task = db.query(Task).filter(Task.id == uuid.UUID(research_task["id"])).first()
            if db_task:
                db_task.status = "in_progress"
                db.commit()
                
            reply_content = researcher.perform_research(request.message)
            
            # Mark the task as completed in DB
            if db_task:
                db_task.status = "completed"
                db.commit()
                
            # Update task status in plan response list
            for t in plan["tasks"]:
                if t["id"] == research_task["id"]:
                    t["status"] = "completed"
        else:
            # Standard reply fallback
            reply_content = f"I've initialized the goal: '{plan['goal']}'. I have created {len(plan['tasks'])} subtasks to execute."
            
        # Optional: Speak reply
        text_to_speech.speak("I have finished analyzing your query.")


    # 5. Store Assistant Message
    jarvis_msg = Message(
        conversation_id=conversation.id,
        sender="jarvis",
        content=reply_content,
        thought_trace=str(plan)
    )
    db.add(jarvis_msg)
    db.commit()

    return {
        "conversation_id": conv_id,
        "reply": reply_content,
        "plan": plan
    }

@app.get("/api/chat/history")
def get_chat_history(db: Session = Depends(get_db)):
    conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    return [{"id": str(c.id), "title": c.title, "created_at": c.created_at} for c in conversations]

@app.get("/api/chat/history/{conv_id}")
def get_conversation_history(conv_id: str, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == uuid.UUID(conv_id)).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at.asc()).all()
    return [
        {
            "id": str(m.id),
            "sender": m.sender,
            "content": m.content,
            "thought_trace": m.thought_trace,
            "created_at": m.created_at
        } for m in messages
    ]

@app.get("/api/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "agent": t.assigned_agent,
            "created_at": t.created_at
        } for t in tasks
    ]

@app.post("/api/tasks")
def create_new_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status="pending",
        assigned_agent=task_data.assigned_agent
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": str(task.id), "title": task.title, "status": task.status}

@app.post("/api/vision/capture")
def trigger_screen_analysis():
    screenshot_name = "current_screen.png"
    success = vision_agent.capture_screen(screenshot_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to capture screen.")
    
    explanation = vision_agent.explain_screen(screenshot_name)
    
    # Remove screen capture after explanation to keep directory clean
    if os.path.exists(screenshot_name):
        try:
            os.remove(screenshot_name)
        except Exception:
            pass
            
    return {"explanation": explanation}

@app.post("/api/audio/tts")
def speak_text(text: str):
    success = text_to_speech.speak(text)
    return {"success": success}

# WebSocket Endpoint for streaming audio input
@app.websocket("/api/audio/stream")
async def websocket_audio_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("Audio streaming WebSocket connection opened.")
    try:
        while True:
            # Receive raw binary audio data
            data = await websocket.receive_bytes()
            # Transcribe audio chunk using speech_to_text
            text = speech_to_text.transcribe_audio_bytes(data)
            # Send back the transcribed text if any was resolved
            if text:
                await websocket.send_json({"text": text})
    except WebSocketDisconnect:
        logger.info("Audio streaming WebSocket connection closed.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
