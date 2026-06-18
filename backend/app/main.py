import os
import uuid
import logging
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db, Conversation, Message, Task, Memory, AuditLog, SessionLocal
from backend.app.agents.planner import PlannerAgent
from backend.app.agents.vision_agent import vision_agent
from backend.app.services.voice.tts import text_to_speech
from backend.app.services.voice.stt import speech_to_text
from backend.app.services.executive.router import CognitiveRouter
from backend.app.api.memory import router as memory_router
from backend.app.api.identity import router as identity_router
from backend.app.api.pcc import router as pcc_router
from backend.app.api.executive import router as executive_router
from backend.app.api.research import router as research_router
from backend.app.api.voice import router as voice_router
from backend.app.api.automation import router as automation_router
from backend.app.api.world_model import router as world_model_router






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

# Register API Routers
app.include_router(memory_router)
app.include_router(identity_router)
app.include_router(pcc_router)
app.include_router(executive_router)
app.include_router(research_router)
app.include_router(voice_router)
app.include_router(automation_router)
app.include_router(world_model_router)




# Initialize Core Agent
planner = PlannerAgent()

def run_async_planning_or_research(conversation_id: str, message: str, is_research: bool):
    """
    Background worker task to execute deep planning or research,
    storing the final result back in the Message history when ready.
    """
    logger.info(f"Running background processing (is_research={is_research}) for convo {conversation_id}")
    db = SessionLocal()
    try:
        import json
        if is_research:
            from backend.app.agents.researcher import ResearchAgent
            researcher = ResearchAgent()
            reply = researcher.perform_research(message)
            plan = {"goal": f"Web Research: {message[:40]}...", "tasks": []}
        else:
            plan = planner.create_plan(message, db)
            # Check for research subtasks
            research_task = next((t for t in plan["tasks"] if t["agent"] == "researcher"), None)
            if research_task:
                from backend.app.agents.researcher import ResearchAgent
                researcher = ResearchAgent()
                
                # Mark as in_progress
                db_task = db.query(Task).filter(Task.id == uuid.UUID(research_task["id"])).first()
                if db_task:
                    db_task.status = "in_progress"
                    db.commit()
                
                reply = researcher.perform_research(message)
                
                # Mark as completed
                if db_task:
                    db_task.status = "completed"
                    db.commit()
                for t in plan["tasks"]:
                    if t["id"] == research_task["id"]:
                        t["status"] = "completed"
            else:
                reply = f"I've initialized the goal: '{plan['goal']}'. I have created {len(plan['tasks'])} subtasks to execute."
                
        # Save final response
        jarvis_msg = Message(
            conversation_id=uuid.UUID(conversation_id),
            sender="jarvis",
            content=reply,
            thought_trace=json.dumps(plan) if isinstance(plan, dict) else str(plan)
        )
        db.add(jarvis_msg)
        db.commit()
        logger.info(f"Background task finished and logged for convo {conversation_id}")
    except Exception as e:
        logger.error(f"Error in background task execution: {e}")
    finally:
        db.close()

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
def post_chat_message(request: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Primary endpoint for user text input. Triggers RCE path evaluations and timeout handling.
    """
    logger.info(f"Received message: {request.message} in conversation: {request.conversation_id}")
    import json
    
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

    # 3. Evaluate path (Path 1 to 4)
    is_fast, fast_reply, fast_plan, path = CognitiveRouter.evaluate_path(request.message, db)
    
    if is_fast:
        # Path 1 or 2: Instant/Fast Response
        jarvis_msg = Message(
            conversation_id=conversation.id,
            sender="jarvis",
            content=fast_reply,
            thought_trace=json.dumps(fast_plan) if isinstance(fast_plan, dict) else str(fast_plan)
        )
        db.add(jarvis_msg)
        db.commit()
        
        # Trigger quick speak
        text_to_speech.speak(fast_reply)
        
        return {
            "conversation_id": conv_id,
            "reply": fast_reply,
            "plan": fast_plan,
            "status": "completed"
        }
        
    # Path 4: Research Mode (<60s)
    if path == 4:
        inter_reply = "I am researching this. Initial findings will be available shortly."
        jarvis_msg = Message(
            conversation_id=conversation.id,
            sender="jarvis",
            content=inter_reply,
            thought_trace=json.dumps({"status": "processing"})
        )
        db.add(jarvis_msg)
        db.commit()
        
        # Delegate to background task
        background_tasks.add_task(run_async_planning_or_research, conv_id, request.message, True)
        
        return {
            "conversation_id": conv_id,
            "reply": inter_reply,
            "plan": {"goal": "Triggered background web research", "tasks": []},
            "status": "processing"
        }
        
    # Path 3: Deep Thinking (<20s) with 10s synchronous timeout
    if path == 3:
        import concurrent.futures
        
        def run_planner_sync():
            db_sync = SessionLocal()
            try:
                plan_result = planner.create_plan(request.message, db_sync)
                research_task = next((t for t in plan_result["tasks"] if t["agent"] == "researcher"), None)
                
                if research_task:
                    from backend.app.agents.researcher import ResearchAgent
                    researcher = ResearchAgent()
                    
                    db_task = db_sync.query(Task).filter(Task.id == uuid.UUID(research_task["id"])).first()
                    if db_task:
                        db_task.status = "in_progress"
                        db_sync.commit()
                        
                    reply = researcher.perform_research(request.message)
                    
                    if db_task:
                        db_task.status = "completed"
                        db_sync.commit()
                    for t in plan_result["tasks"]:
                        if t["id"] == research_task["id"]:
                            t["status"] = "completed"
                else:
                    reply = f"I've initialized the goal: '{plan_result['goal']}'. I have created {len(plan_result['tasks'])} subtasks to execute."
                return plan_result, reply
            finally:
                db_sync.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_planner_sync)
            try:
                # Enforce 10s timeout policy
                plan_result, reply = future.result(timeout=10.0)
                
                # Save final response
                jarvis_msg = Message(
                    conversation_id=conversation.id,
                    sender="jarvis",
                    content=reply,
                    thought_trace=json.dumps(plan_result) if isinstance(plan_result, dict) else str(plan_result)
                )
                db.add(jarvis_msg)
                db.commit()
                
                # Trigger speak
                text_to_speech.speak("I have finished analyzing your query.")
                
                return {
                    "conversation_id": conv_id,
                    "reply": reply,
                    "plan": plan_result,
                    "status": "completed"
                }
            except concurrent.futures.TimeoutError:
                # Over 10 seconds timeout limit: send progressive warning and run async
                logger.info(f"Convo {conv_id} planner exceeded 10s. Sending warning and routing to background worker.")
                inter_reply = "I am researching this. Initial findings will be available shortly."
                jarvis_msg = Message(
                    conversation_id=conversation.id,
                    sender="jarvis",
                    content=inter_reply,
                    thought_trace=json.dumps({"status": "processing"})
                )
                db.add(jarvis_msg)
                db.commit()
                
                # Delegate to background task
                background_tasks.add_task(run_async_planning_or_research, conv_id, request.message, False)
                
                return {
                    "conversation_id": conv_id,
                    "reply": inter_reply,
                    "plan": {"goal": "Deep thinking task routed to background", "tasks": []},
                    "status": "processing"
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

# Reload comment trigger

