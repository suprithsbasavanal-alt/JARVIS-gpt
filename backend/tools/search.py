import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs a web search using the free duckduckgo-search package.
    Returns a list of dicts with keys: 'title', 'href', 'body'.
    """
    logger.info(f"Performing web search for: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                }
                for r in results
            ]
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        # Fallback to general search stub
        return [
            {
                "title": f"Mock search result for {query}",
                "href": "https://example.com/search",
                "body": f"Unable to perform active web search due to error: {e}. Please ensure network connection is available."
            }
        ]
