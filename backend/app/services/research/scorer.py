import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SourceCredibilityScorer:
    # Pre-defined domain rules
    HIGH_CREDIBILITY_DOMAINS = {
        "wikipedia.org", "github.com", "stackoverflow.com", "arxiv.org", 
        "w3.org", "python.org", "rust-lang.org", "sqlite.org", "postgresql.org",
        "oracle.com", "microsoft.com", "developer.apple.com", "developer.android.com",
        "aws.amazon.com", "cloud.google.com", "mozilla.org", "ietf.org", "pypi.org",
        "npmtreds.com", "npmjs.com", "go.dev", "pkg.go.dev"
    }
    
    MEDIUM_CREDIBILITY_DOMAINS = {
        "medium.com", "dev.to", "reddit.com", "news.ycombinator.com", "hackernews.com",
        "techcrunch.com", "wired.com", "theverge.com", "arstechnica.com", "infoq.com",
        "dzone.com", "towardsdatascience.com", "freecodecamp.org", "geeksforgeeks.org"
    }

    @classmethod
    def score_source(cls, url: str) -> float:
        """
        Calculates a credibility score between 0.0 and 1.0 for a source URL.
        """
        if not url:
            return 0.4
            
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
                
            # Check for exact matches
            if domain in cls.HIGH_CREDIBILITY_DOMAINS:
                return 1.0
            if domain in cls.MEDIUM_CREDIBILITY_DOMAINS:
                return 0.75
                
            # Check for tld suffixes (.gov, .edu)
            if domain.endswith(".gov") or domain.endswith(".edu") or domain.endswith(".mil"):
                return 1.0
            if domain.endswith(".org"):
                return 0.85
                
            # Subdomain checks (e.g. docs.python.org, developer.mozilla.org)
            for high_d in cls.HIGH_CREDIBILITY_DOMAINS:
                if domain.endswith(f".{high_d}"):
                    return 1.0
                    
            for med_d in cls.MEDIUM_CREDIBILITY_DOMAINS:
                if domain.endswith(f".{med_d}"):
                    return 0.75
        except Exception as e:
            logger.warning(f"Error parsing domain for credibility score of '{url}': {e}")
            
        # Default low-credibility score for unknown/general domains
        return 0.5

class ConfidenceScoringEngine:
    @staticmethod
    def calculate_confidence(
        sources: list[dict], 
        contradiction_count: int, 
        total_claims_count: int
    ) -> float:
        """
        Calculates an aggregate confidence score (0.0 to 1.0) based on:
        - Average source credibility
        - Number of unique sources (source variety)
        - Percentage of conflicting claims (agreement rate)
        """
        if not sources:
            return 0.0
            
        # 1. Average Source Credibility
        total_cred = sum(SourceCredibilityScorer.score_source(s.get("href", "")) for s in sources)
        avg_credibility = total_cred / len(sources)
        
        # 2. Source Variety (rewarding up to 5 unique sources)
        source_count = len(sources)
        variety_factor = min(source_count / 5.0, 1.0)
        
        # 3. Contradiction Penalty
        if total_claims_count > 0:
            contradiction_rate = contradiction_count / total_claims_count
            agreement_factor = max(1.0 - (contradiction_rate * 2.0), 0.0) # Conflicting data penalizes heavily
        else:
            agreement_factor = 1.0
            
        # Weighted aggregate score
        # 40% credibility, 30% variety, 30% agreement
        raw_confidence = (avg_credibility * 0.4) + (variety_factor * 0.3) + (agreement_factor * 0.3)
        confidence = round(max(min(raw_confidence, 1.0), 0.0), 2)
        
        logger.info(
            f"Confidence calculated: {confidence} "
            f"(Credibility: {avg_credibility:.2f}, Variety Factor: {variety_factor:.2f}, Agreement Factor: {agreement_factor:.2f})"
        )
        return confidence
