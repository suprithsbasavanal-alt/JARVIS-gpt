"""
agents/master_agent.py
The central cognitive router for JARVIS. 
It analyzes the user's intent and delegates the task to the appropriate specialized sub-agent.
"""
import brain.llm as llm
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent

class MasterAgent:
    def __init__(self):
        self.coding_agent = CodingAgent()
        self.research_agent = ResearchAgent()

    def process_request(self, user_input):
        """Routes the prompt to the correct agent based on keyword heuristics or LLM intent parsing."""
        lower_input = user_input.lower()
        
        # Simple heuristic routing for high speed
        if any(keyword in lower_input for keyword in ["code", "script", "python", "html", "css", "debug", "compile"]):
            return self.coding_agent.execute(user_input)
            
        elif any(keyword in lower_input for keyword in ["research", "explain", "summarize", "find out", "who is", "what is"]):
            return self.research_agent.execute(user_input)
            
        else:
            # Default to general conversational brain
            print("[AGENT] Routing to General Brain...")
            return llm.generate_response(user_input)

# Global singleton instance
master = MasterAgent()
