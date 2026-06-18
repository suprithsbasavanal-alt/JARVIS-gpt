import logging
import google.generativeai as genai
from backend.config import settings

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
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
        
        # Mock responses when API is missing
        return f"[Agent {self.name} mock response to: '{prompt}']"
