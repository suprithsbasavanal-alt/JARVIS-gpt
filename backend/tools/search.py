import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

_search_cache = {}

def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs a web search using the free duckduckgo-search package.
    Returns a list of dicts with keys: 'title', 'href', 'body'.
    Caches search results to prevent rate limiting on repeat queries.
    """
    normalized_query = query.strip().lower()
    if normalized_query in _search_cache:
        logger.info(f"Serving cached search results for: '{query}'")
        return _search_cache[normalized_query]

    logger.info(f"Performing web search for: '{query}'")
    try:
        with DDGS() as ddgs:
            # Try html backend first since it is more reliable, fallback to default auto
            try:
                results = list(ddgs.text(query, max_results=max_results, backend="html"))
            except Exception:
                results = list(ddgs.text(query, max_results=max_results))
                
            parsed_results = [
                {
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                }
                for r in results
            ]
            if parsed_results:
                _search_cache[normalized_query] = parsed_results
                return parsed_results
            else:
                raise Exception("DuckDuckGo returned empty results.")
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
