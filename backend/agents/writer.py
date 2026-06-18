from backend.agents.base import BaseAgent

WRITER_PROMPT = """You are the JARVIS Writing Agent. Your task is to write emails, prepare outlines, compose summaries, edit reports, and format Markdown files.
Maintain an engaging, clear, and professional tone.
"""

class WritingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="writer",
            system_prompt=WRITER_PROMPT
        )
