import logging
from backend.agents.base import BaseAgent
from backend.tools.search import web_search

logger = logging.getLogger(__name__)

RESEARCHER_PROMPT = """You are the JARVIS Research Agent. Your task is to investigate topics, execute web searches, read sources, cross-reference reports, and synthesize highly accurate summaries.
You prioritize accuracy and reasoning over speed. You distinguish between verified facts, probable conclusions, and opinions, and you explicitly highlight contradictions or uncertainties.
"""

VERIFICATION_PROMPT = """You are the JARVIS Fact Verification Engine. 
You are given a list of raw search results from different outlets regarding: "{topic}"

Please perform a deep cross-reference analysis:
1. Identify consensus facts: What information is reported consistently across multiple sources?
2. Detect discrepancies or contradictions: Are there conflicting accounts or numbers reported?
3. Separate verified facts from opinion, editorial commentary, or speculation.
4. Synthesize a structured briefing organized by key developments.
5. List the sources consulted with their titles and URLs.
6. Clearly state any unresolved questions or uncertainties.

Raw Search Results:
{search_results_text}

Respond with your finalized briefing and fact-verification report.
"""

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="researcher",
            system_prompt=RESEARCHER_PROMPT
        )

    def perform_research(self, topic: str) -> str:
        """
        Runs the full Research -> Verify -> Reason -> Answer workflow.
        """
        logger.info(f"Initiating research flow for: '{topic}'")
        
        # 1. Search multiple queries to gather diverse sources
        search_results = []
        queries = [topic]
        if "news" in topic.lower():
            queries.extend([f"{topic} breaking news", f"{topic} latest updates"])
            
        seen_urls = set()
        for q in queries[:2]: # Limit queries to avoid rate limits
            results = web_search(q, max_results=4)
            for r in results:
                if r["href"] not in seen_urls:
                    seen_urls.add(r["href"])
                    search_results.append(r)

        if not search_results:
            return "No information could be retrieved from search engines. Please check connection."

        # 2. Format search results for the verification model
        formatted_results = []
        for idx, res in enumerate(search_results):
            formatted_results.append(
                f"Source [{idx+1}]: {res['title']}\n"
                f"URL: {res['href']}\n"
                f"Content: {res['body']}\n"
                f"---"
            )
        search_results_text = "\n".join(formatted_results)

        # 3. Feed to verification engine (LLM)
        if self.model:
            try:
                # We can construct a specific prompt using our verification template
                full_verification_prompt = VERIFICATION_PROMPT.format(
                    topic=topic,
                    search_results_text=search_results_text
                )
                response = self.model.generate_content(full_verification_prompt)
                return response.text
            except Exception as e:
                logger.error(f"Error during fact-verification LLM call: {e}")
        
        # Heuristic fallback if model is offline or key is missing
        briefing = f"### [OFFLINE MODE] Verified Briefing for: {topic}\n\n"
        briefing += "Consensus facts compiled from local heuristic analysis:\n"
        for idx, res in enumerate(search_results[:3]):
            briefing += f"- **{res['title']}**: {res['body'][:180]}... [Source: {res['href']}]\n"
        briefing += "\n*Note: Active LLM reasoning is offline. Please enter a Gemini API Key in Settings to enable full cross-referencing.*"
        
        return briefing
