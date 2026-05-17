"""
agents/research_agent.py
A specialized sub-agent for analyzing information and web research summaries.
"""
import brain.llm as llm
import utils.internet as internet

class ResearchAgent:
    def __init__(self):
        self.system_prompt = (
            "You are JARVIS-RESEARCH, an advanced AI intelligence analyst. "
            "Your purpose is to ingest data and provide highly accurate, concise, and insightful summaries. "
            "Respond in a professional, cinematic tone like you are briefing a CEO or Commander."
        )

    def execute(self, user_prompt):
        """Processes an information or research query."""
        print("[AGENT] Routing to Research Agent...")
        
        # If the user specifically asks to search google, we fetch the data first
        if "search google" in user_prompt.lower():
            # In a full implementation, we'd scrape the page. For now, we rely on the internet tool.
            query = user_prompt.lower().replace("search google for", "").strip()
            return internet.search_google(query)
            
        enhanced_prompt = f"Analyze the following query and provide a definitive answer: {user_prompt}"
        return llm.generate_response(enhanced_prompt, custom_system_prompt=self.system_prompt)
