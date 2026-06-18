import logging
from urllib.parse import urlparse
from backend.app.services.research.search import web_search

logger = logging.getLogger(__name__)

class MultiSourceCollector:
    @staticmethod
    def collect_sources(query: str, max_results_per_query: int = 5) -> list[dict]:
        """
        Executes search for the main query and supplementary queries
        to build a robust, multi-perspective set of raw results.
        """
        logger.info(f"Collecting sources for query: '{query}'")
        
        # Determine helper queries to broaden research scope
        queries = [query]
        query_lower = query.lower()
        
        # Add supplementary search terms depending on type of question
        if "news" in query_lower or "release" in query_lower or "latest" in query_lower:
            queries.append(f"{query} latest news updates")
            queries.append(f"{query} announcement details")
        elif "vs" in query_lower or "difference" in query_lower or "compare" in query_lower:
            queries.append(f"{query} comparison review")
        elif "error" in query_lower or "failed" in query_lower or "issue" in query_lower:
            queries.append(f"{query} solution fix discussion")
        else:
            queries.append(f"{query} overview documentation")
            
        all_results = []
        for q in queries[:3]: # Limit to max 3 queries to avoid aggressive rate limiting
            try:
                results = web_search(q, max_results=max_results_per_query)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Search query '{q}' failed: {e}")
                
        return all_results

class DuplicateDetectionEngine:
    @staticmethod
    def remove_duplicates(results: list[dict], similarity_threshold: float = 0.75) -> list[dict]:
        """
        Deduplicates search results by URL and content text similarity.
        """
        unique_results = []
        seen_urls = set()
        seen_bodies = []
        
        for r in results:
            url = r.get("href", "").strip().lower()
            body = r.get("body", "").strip()
            
            # 1. URL Deduplication
            if not url or url in seen_urls:
                continue
                
            # Normalize URL to catch variations (e.g. trailing slashes, http vs https)
            parsed = urlparse(url)
            norm_url = f"{parsed.netloc}{parsed.path.rstrip('/')}"
            if norm_url in seen_urls:
                continue
                
            # 2. Text Content Deduplication (Jaccard similarity on lowercased words)
            is_duplicate = False
            words = set(body.lower().split())
            if len(words) > 5:  # Only check substantial text bodies
                for seen_w in seen_bodies:
                    if not seen_w:
                        continue
                    intersection = len(words.intersection(seen_w))
                    union = len(words.union(seen_w))
                    similarity = intersection / union if union > 0 else 0
                    if similarity > similarity_threshold:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                seen_urls.add(url)
                seen_urls.add(norm_url)
                seen_bodies.append(words)
                unique_results.append(r)
                
        logger.info(f"Deduplicated sources: {len(results)} raw -> {len(unique_results)} unique")
        return unique_results
