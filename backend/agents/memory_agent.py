import logging
from sqlalchemy.orm import Session
from backend.agents.base import BaseAgent
from backend.database import Memory
from backend.memory import memory_store

logger = logging.getLogger(__name__)

MEMORY_PROMPT = """You are the JARVIS Memory Agent. Your task is to maintain user preferences, project knowledge, facts, and habits.
Extract key facts from the conversation history, identify user preferences, and return them in a structured key-value format.
"""

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="memory",
            system_prompt=MEMORY_PROMPT
        )

    def extract_and_save_facts(self, conversation_text: str, db: Session):
        """
        Extract key facts from conversation text and save them.
        """
        logger.info("Extracting and saving facts from conversation...")
        # Placeholder for LLM extraction
        # e.g., "The user is working on a final year project called JARVIS-gpt"
        # We would write this to database and vectorize it for Qdrant
        
        # Simple local test save
        try:
            pref = Memory(
                entity_key="last_active_project",
                entity_value="JARVIS-gpt",
                category="project"
            )
            # Merge to handle conflicts
            db.merge(pref)
            db.commit()
            
            # Save to Qdrant (using a mock vector for testing)
            mock_vector = [0.1] * 1536
            memory_store.add_memory(
                text="The user is working on a final year project called JARVIS-gpt.",
                vector=mock_vector,
                metadata={"category": "project", "source": "conversation"}
            )
            logger.info("Saved memory fact successfully.")
        except Exception as e:
            logger.error(f"Failed to save memory fact: {e}")

memory_agent = MemoryAgent()
