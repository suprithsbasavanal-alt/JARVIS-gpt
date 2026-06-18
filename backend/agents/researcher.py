from backend.agents.base import BaseAgent

RESEARCHER_PROMPT = """You are the JARVIS Research Agent. Your task is to investigate topics, search the web, read files/documents, and synthesize information into clean, summarized reports for the planner or user.
Always structure your research logically with headings, bullet points, and key findings.
"""

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="researcher",
            system_prompt=RESEARCHER_PROMPT
        )
