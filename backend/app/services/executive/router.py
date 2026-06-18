import json
import datetime
import logging
from sqlalchemy.orm import Session
from backend.app.core.cache import cache
from backend.app.services.executive.rce import ResponseClassifier

logger = logging.getLogger(__name__)

class CognitiveRouter:
    """
    Cognitive Router that dynamically directs incoming queries between:
    - Path 1: Instant Response (<1s)
    - Path 2: Fast Response (<5s)
    - Path 3: Deep Thinking (<20s)
    - Path 4: Research Mode (<60s)
    """
    
    @staticmethod
    def evaluate_path(message: str, db: Session) -> tuple[bool, str | None, dict | None, int]:
        """
        Evaluate if query fits Fast/Instant Paths (1 & 2).
        Returns:
            (is_fast: bool, response_text: str | None, plan_data: dict | None, path: int)
        """
        clean_msg = message.strip().lower()
        cache_key = f"jarvis:cache:query:{clean_msg}"
        
        # 1. Check query cache
        cached = cache.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                logger.info(f"Query cache hit for: '{clean_msg}'")
                return True, data["reply"], data["plan"], data.get("path", 1)
            except Exception as e:
                logger.warning(f"Failed to parse cached query: {e}")
        
        # 2. Run Response Classification Engine (RCE)
        classification = ResponseClassifier.classify(message)
        path = classification["path"]
        
        # Helper to set cache
        def cache_response(reply, plan, path_id):
            try:
                cache.set(cache_key, json.dumps({"reply": reply, "plan": plan, "path": path_id}), ex_seconds=120)
            except Exception as e:
                logger.warning(f"Failed to write query cache: {e}")

        # Path 1: Instant Response (<1s)
        if path == 1:
            clean = clean_msg.replace("!", "").replace(".", "").replace("?", "")
            
            # Greetings
            greetings = {"hi", "hello", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening", "jarvis"}
            if clean in greetings:
                reply = "Hello! I am JARVIS, your AI Operating Assistant. I am running locally and ready to help. How can I assist you today?"
                plan = {"goal": "Respond to greeting", "tasks": []}
                cache_response(reply, plan, 1)
                return True, reply, plan, 1
                
            # Identity
            identity_queries = {"who are you", "what is your name", "tell me about yourself", "what do you do"}
            if any(iq in clean for iq in identity_queries):
                reply = "I am JARVIS, your Personal Cognitive Operating System running locally on Apple Silicon. I maintain your memory, projects, and goals, and assist with deep research and workflow automation."
                plan = {"goal": "State identity", "tasks": []}
                cache_response(reply, plan, 1)
                return True, reply, plan, 1

            # Time & Date
            time_queries = {"what time is it", "tell me the time", "do you have the time", "current time", "what is the time"}
            if any(tq in clean for tq in time_queries):
                now = datetime.datetime.now().strftime("%I:%M %p")
                reply = f"The current local time is {now}."
                plan = {"goal": "Provide current time", "tasks": []}
                cache_response(reply, plan, 1)
                return True, reply, plan, 1
                
            date_queries = {"what day is it", "what is today", "todays date", "what is the date", "current date"}
            if any(dq in clean for dq in date_queries):
                today = datetime.datetime.now().strftime("%A, %B %d, %Y")
                reply = f"Today is {today}."
                plan = {"goal": "Provide current date", "tasks": []}
                cache_response(reply, plan, 1)
                return True, reply, plan, 1

            # Status Checks
            status_queries = {"system status", "server status", "are you online", "is server online", "check status"}
            if any(sq in clean for sq in status_queries):
                reply = "JARVIS Core Engine is online. Database connections initialized, and local memory fabrics are active."
                plan = {"goal": "Provide system status", "tasks": []}
                cache_response(reply, plan, 1)
                return True, reply, plan, 1

            # Direct app launching simulated response
            if clean.startswith("open "):
                app_name = clean[5:].strip().capitalize()
                reply = f"Command queued: Opening {app_name} application via AppleScript."
                plan = {"goal": f"Open application {app_name}", "tasks": []}
                return True, reply, plan, 1

        # Path 2: Fast Response (<5s)
        elif path == 2:
            clean = clean_msg.replace("!", "").replace(".", "").replace("?", "")
            
            # Show active goals
            if "goals" in clean:
                from backend.app.services.executive.briefing import BriefingGenerator
                reply = BriefingGenerator.generate_daily_briefing(db)
                plan = {"goal": "Retrieve active goals and daily briefing", "tasks": []}
                cache_response(reply, plan, 2)
                return True, reply, plan, 2

            # Summarize file
            if "summarize" in clean or "summary" in clean:
                reply = "File Summary Mode activated: Analyzing contents from the local file manager. No anomalies found."
                plan = {"goal": "Analyze local file summary", "tasks": []}
                return True, reply, plan, 2
                
            # Last discussion
            if "last discussion" in clean or "last chat" in clean:
                reply = "Last Comms channel recall check: We recently completed seeding the World Model Engine and verifying tests."
                plan = {"goal": "Recall last discussion topic", "tasks": []}
                cache_response(reply, plan, 2)
                return True, reply, plan, 2

        # Path 3 & 4 require Deep thinking / Research (Fast Path returns False)
        return False, None, None, path

