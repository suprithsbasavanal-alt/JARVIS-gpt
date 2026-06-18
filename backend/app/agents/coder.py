from backend.app.agents.base import BaseAgent

CODER_PROMPT = """You are the JARVIS Coding Agent. Write clean, correct, and modern code, analyze and debug software errors, and design folder structures.
Ensure code changes are structured as diffs or functional blocks. Maintain logical brevity and objective alignment.
"""

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="coder",
            system_prompt=CODER_PROMPT
        )
