import datetime
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class CognitiveRouter:
    """
    Cognitive Router that dynamically directs incoming queries between:
    - Fast Path: Simple questions, greetings, system status, local time, and immediate actions.
    - Deep Thinking Path: Strategic goal-planning, research, multi-agent execution, and memory synthesis.
    """
    
    @staticmethod
    def evaluate_path(message: str, db: Session) -> tuple[bool, str | None, dict | None]:
        """
        Evaluate if query fits Fast Path.
        Returns:
            (is_fast: bool, response_text: str | None, plan_data: dict | None)
        """
        clean = message.strip().lower().replace("!", "").replace(".", "").replace("?", "")
        
        # 0. Daily Briefing & Priorities Hooks
        briefing_queries = {
            "what should i work on today", 
            "what should i work on", 
            "daily briefing", 
            "show my priorities", 
            "show priorities", 
            "what are my priorities", 
            "priorities"
        }
        if any(bq in clean for bq in briefing_queries):
            from backend.app.services.executive.briefing import BriefingGenerator
            briefing = BriefingGenerator.generate_daily_briefing(db)
            return True, briefing, {"goal": "Provide strategic daily briefing", "tasks": []}
        
        # 1. Greetings & Identity
        greetings = {"hi", "hello", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening", "jarvis"}
        if clean in greetings:
            return True, "Hello! I am JARVIS, your AI Operating Assistant. I am running locally and ready to help. How can I assist you today?", {"goal": "Respond to greeting", "tasks": []}
            
        identity_queries = {"who are you", "what is your name", "tell me about yourself", "what do you do"}
        if any(iq in clean for iq in identity_queries):
            return True, "I am JARVIS, your Personal Cognitive Operating System running locally on Apple Silicon. I maintain your memory, projects, and goals, and assist with deep research and workflow automation.", {"goal": "State identity", "tasks": []}

        # 2. Time & Date
        time_queries = {"what time is it", "tell me the time", "do you have the time", "current time", "what is the time"}
        if any(tq in clean for tq in time_queries):
            now = datetime.datetime.now().strftime("%I:%M %p")
            return True, f"The current local time is {now}.", {"goal": "Provide current time", "tasks": []}
            
        date_queries = {"what day is it", "what is today", "todays date", "what is the date", "current date"}
        if any(dq in clean for dq in date_queries):
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return True, f"Today is {today}.", {"goal": "Provide current date", "tasks": []}

        # 3. Quick System Checks
        status_queries = {"system status", "server status", "are you online", "is server online", "check status"}
        if any(sq in clean for sq in status_queries):
            return True, "JARVIS Core Engine is online. Database connections initialized, and local memory fabrics are active.", {"goal": "Provide system status", "tasks": []}

        # Default: Deep Thinking Path required (multi-agent, goal plan, vector database search)
        return False, None, None
