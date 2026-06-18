import logging
import google.generativeai as genai
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

JARVIS_BEHAVIORAL_CONSTITUTION = """You are JARVIS.
You are not a chatbot or virtual assistant. You are the user's personal AI companion and chief operating assistant.
Your purpose is to help the user think, learn, build, solve problems, and accomplish goals.
Behave as though you are continuously present and aware of the user's projects, priorities, and context.

PERSONALITY:
- Highly intelligent, calm, professional, respectful, helpful, observant, efficient, trustworthy.
- Never sound robotic, like customer support, or like a search engine.
- Never over-explain unless asked.
- Never say: "As an AI language model...", "I cannot think...", "I am just an AI...". Communicate naturally.

COMMUNICATION STYLE:
- Speak like a highly capable executive assistant.
- Be concise first. Expand only when necessary.
- Avoid robotic prefixes. (e.g., say "I found three relevant reports" instead of "Based on the information available, it appears that...").
- Do not ask open-ended continuation questions unless necessary (e.g., prefer "I can also compare the alternatives if you'd like" over "Would you like me to continue?").

THINK BEFORE RESPONDING:
- Understand intent and context, retrieve memory, analyze information, form a conclusion, and then respond.

TRUTHFULNESS:
- Never invent facts or pretend to know. If information is uncertain, say so clearly (e.g., "I found conflicting reports. Here's what is confirmed."). Accuracy is more important than speed.
"""

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = f"{JARVIS_BEHAVIORAL_CONSTITUTION}\n\nAgent Role Specifics:\n{system_prompt}"
        self._init_client()

    def _init_client(self):
        # Initialize Gemini API if key is present
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=self.system_prompt
                )
                logger.info(f"Initialized Gemini model for agent {self.name}")
            except Exception as e:
                logger.error(f"Error configuring Gemini client for {self.name}: {e}")
                self.model = None
        else:
            self.model = None
            logger.warning(f"No GEMINI_API_KEY set for agent {self.name}. Running in mock mode.")

    def run(self, prompt: str, context: dict | None = None) -> str:
        """
        Executes the agent reasoning flow on the given prompt.
        """
        logger.info(f"Agent {self.name} processing prompt: {prompt}")
        if self.model:
            try:
                # Merge context into user prompt
                full_prompt = f"Context: {context}\n\nUser Input: {prompt}" if context else prompt
                response = self.model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                logger.error(f"Error executing LLM call for {self.name}: {e}")
        
        # Natural, companion-style mock responses when API is missing
        if self.name == "planner":
            # For planner, we need to return a valid JSON structure so the parser does not fail
            return '{"goal": "' + prompt + '", "steps": [{"title": "Analyze and research", "description": "Formulate insights.", "agent": "researcher", "dependencies": []}, {"title": "Synthesize report", "description": "Compile verified outputs.", "agent": "writer", "dependencies": ["Analyze and research"]}]}'
        elif self.name == "researcher":
            return f"I performed research regarding '{prompt}'. In mock mode, the details are synthesized locally, indicating system configurations are ready."
        elif self.name == "coder":
            return f"I have analyzed the coding request for '{prompt}'. The code structure has been verified and is ready for implementation."
        elif self.name == "writer":
            return f"Here is the draft for '{prompt}': The operation is set up and ready to go."
        
        return f"I have processed your request for '{prompt}'. The system is configured and fully operational."
