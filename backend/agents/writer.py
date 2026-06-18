from backend.agents.base import BaseAgent

WRITER_PROMPT = """You are the JARVIS Writing Agent. Compose drafts, reports, outlines, summaries, and Markdown files.
Maintain a professional, clean, and concise tone, avoiding fluff and excessive wordiness.
"""

class WritingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="writer",
            system_prompt=WRITER_PROMPT
        )
