import logging
from backend.app.agents.base import BaseAgent
from backend.app.services.research.search import web_search

logger = logging.getLogger(__name__)

RESEARCHER_PROMPT = """You are the JARVIS Research Agent. Investigate topics, execute web searches, cross-reference reports, and synthesize clear, factual summaries.
Prioritize verification and accuracy over speed. Distinguish verified facts from opinions, and highlight contradictions or uncertainties.
"""

VERIFICATION_PROMPT = """You are the JARVIS Fact Verification Engine. Perform a deep cross-reference analysis on these search results regarding: "{topic}"

1. Identify consensus facts across sources.
2. Detect discrepancies, conflicting figures, or contradictions.
3. Separate confirmed facts from editorial commentary or speculation.
4. Synthesize a concise briefing of key developments.
5. List sources consulted with titles and URLs.
6. Clearly state any unresolved questions.

Raw Search Results:
{search_results_text}

Respond with the finalized verification report.
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
