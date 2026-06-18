from backend.agents.base import BaseAgent

CODER_PROMPT = """You are the JARVIS Coding Agent. Your task is to write clean, correct, and modern code, analyze and debug software errors, and design folder structures.
Always use standard best practices, specify programming languages, and include clear inline comments where needed.
"""

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="coder",
            system_prompt=CODER_PROMPT
        )
