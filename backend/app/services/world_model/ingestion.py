import logging
import re
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class RSSIngestor:
    @staticmethod
    def fetch_and_parse(url: str) -> list[dict]:
        """
        Fetches an RSS/XML feed from url and parses items.
        Falls back to mock/simulated feed items if offline or on error.
        """
        logger.info(f"Ingesting feed from: {url}")
        
        # Simulated responses for testing or offline environments
        if "mock" in url or not url.startswith("http"):
            return RSSIngestor._get_mock_items(url)
            
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            items = []
            
            # RSS typically has channel/item structure
            for item in root.findall(".//item"):
                title = item.find("title")
                description = item.find("description")
                link = item.find("link")
                pubDate = item.find("pubDate")
                
                items.append({
                    "title": title.text.strip() if title is not None and title.text else "",
                    "description": description.text.strip() if description is not None and description.text else "",
                    "source_url": link.text.strip() if link is not None and link.text else "",
                    "pub_date": pubDate.text.strip() if pubDate is not None and pubDate.text else ""
                })
            return items
        except Exception as e:
            logger.warning(f"Failed to fetch or parse RSS from '{url}': {e}. Falling back to mock data.")
            return RSSIngestor._get_mock_items(url)

    @staticmethod
    def _get_mock_items(url: str) -> list[dict]:
        """
        Returns mock RSS feed items based on the type of URL.
        """
        if "security" in url or "cve" in url:
            return [
                {
                    "title": "CVE-2026-9988: Critical RCE vulnerability detected in FastAPI before v0.120",
                    "description": "A remote code execution vulnerability was identified in FastAPI body parsing queries.",
                    "source_url": "https://nvd.nist.gov/vuln/detail/CVE-2026-9988",
                    "pub_date": "Thu, 18 Jun 2026 12:00:00 GMT"
                },
                {
                    "title": "Unauthenticated access vulnerability in PostgreSQL Docker containers",
                    "description": "An advisory warning for developer databases exposing trust authentication.",
                    "source_url": "https://cisa.gov/advisories/pg-trust",
                    "pub_date": "Wed, 17 Jun 2026 09:00:00 GMT"
                }
            ]
        elif "ai" in url or "hacker" in url:
            return [
                {
                    "title": "Qwen-3 open-source weights officially released by Alibaba Team",
                    "description": "Alibaba releases Qwen-3 models with up to 72B parameters exhibiting SOTA reasoning.",
                    "source_url": "https://github.com/QwenLM/Qwen-3",
                    "pub_date": "Thu, 18 Jun 2026 15:00:00 GMT"
                },
                {
                    "title": "FastAPI v0.122.0 released with native WebSocket compression",
                    "description": "The latest FastAPI version improves real-time WebSocket connection handling.",
                    "source_url": "https://github.com/tiangolo/fastapi/releases",
                    "pub_date": "Thu, 18 Jun 2026 10:00:00 GMT"
                }
            ]
        # General tech updates
        return [
            {
                "title": "Rust 1.95 stabilized with refined constant evaluation",
                "description": "The Rust team stabilizes refined traits for const fn implementations.",
                "source_url": "https://blog.rust-lang.org/2026/06/18/Rust-1.95.html",
                "pub_date": "Thu, 18 Jun 2026 14:00:00 GMT"
            }
        ]

class TrendFilter:
    # Category keyword mapping
    AI_RELEASE_KEYWORDS = ["model", "llm", "llama", "qwen", "openai", "deepseek", "generative ai", "claude", "gemini", "weights", "release"]
    SECURITY_KEYWORDS = ["cve", "vulnerability", "cisa", "exploit", "leak", "hack", "zero-day", "security advisory", "advisory", "rce"]
    TECH_TREND_KEYWORDS = ["framework", "library", "rust", "python", "typescript", "fastapi", "web", "speedup", "benchmark", "stabilized"]

    @classmethod
    def classify_item(cls, title: str, description: str) -> str:
        """
        Classifies an item based on keywords in title or description.
        """
        text = f"{title} {description}".lower()
        
        def has_keyword(keywords, text):
            for kw in keywords:
                # Match with word boundaries
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text):
                    return True
            return False

        # Check security first (higher priority)
        if has_keyword(cls.SECURITY_KEYWORDS, text):
            return "Security Vulnerability"
            
        if has_keyword(cls.AI_RELEASE_KEYWORDS, text):
            return "AI Release"
            
        if has_keyword(cls.TECH_TREND_KEYWORDS, text):
            return "Tech Trend"
            
        return "General"
