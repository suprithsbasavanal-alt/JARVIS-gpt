import re
import logging

logger = logging.getLogger(__name__)

class ResponseClassifier:
    """
    Response Classification Engine (RCE).
    Classifies incoming user messages into one of four execution paths:
      - PATH 1: Instant Response (<1s)
      - PATH 2: Fast Response (<5s)
      - PATH 3: Deep Thinking (<20s)
      - PATH 4: Research Mode (<60s)
    """
    
    @staticmethod
    def classify(message: str) -> dict:
        clean = message.strip().lower().replace("!", "").replace(".", "").replace("?", "")
        
        # 1. Path 1: Instant Response (<1s)
        # greetings, time/date, status, app launching, or quick tasks queries
        instant_keywords = [
            r"^open\s+\w+",
            r"^what\s+time\s+is\s+it",
            r"^current\s+time",
            r"^what\s+is\s+the\s+time",
            r"^what\s+day\s+is\s+it",
            r"^what\s+is\s+today",
            r"^what\s+is\s+the\s+date",
            r"^system\s+status",
            r"^server\s+status",
            r"^hi$", r"^hello$", r"^hey$", r"^yo$"
        ]
        for pattern in instant_keywords:
            if re.search(pattern, clean):
                return {
                    "path": 1,
                    "target_latency": "< 1s",
                    "reason": "Matched instant greeting/status/time/app query patterns."
                }
                
        # 2. Path 4: Research Mode (<60s)
        # Real-time search/telemetry queries (news, security alerts, vulnerabilities, CVEs, or real-time topics)
        research_keywords = [
            "news", "cve", "vulnerability", "vulnerabilities", "exploit", 
            "latest", "realtime", "real-time", "today's", "security advisory"
        ]
        if any(kw in clean for kw in research_keywords) or clean.startswith("research "):
            return {
                "path": 4,
                "target_latency": "< 60s",
                "reason": "Query requests real-time feed telemetry or security vulnerabilities."
            }

        # 3. Path 2: Fast Response (<5s)
        # Summaries, historical conversation queries, active goal retrieval
        fast_keywords = [
            "summarize", "summary", "last discussion", "last chat", "active goals", 
            "my goals", "what is my goal", "active projects", "my projects"
        ]
        if any(kw in clean for kw in fast_keywords):
            return {
                "path": 2,
                "target_latency": "< 5s",
                "reason": "Matched historical recall, active goal list, or file summary."
            }
            
        # 4. Path 3: Deep Thinking (<20s)
        # Default for complex, conceptual, architectural, or planning queries
        # (e.g. comparing architectures, code refactoring, problem solving)
        return {
            "path": 3,
            "target_latency": "< 20s",
            "reason": "Defaulted to Deep Thinking Path for planning, coding, or conceptual reasoning."
        }
