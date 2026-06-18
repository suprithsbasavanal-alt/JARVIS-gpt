import logging
import re
import google.generativeai as genai
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

FACT_EXTRACTION_PROMPT = """You are a Fact Extraction Bot. Your task is to extract discrete, factual claims from the text snippet below.
List each fact as a simple statement. Avoid opinions, commentary, or speculations.
Format the output as a JSON list of strings, for example:
[
  "Python 3.13 was released on October 7, 2024.",
  "Python 3.13 introduces a new JIT compiler."
]

Snippet:
"{text}"
"""

CONTRADICTION_DETECTION_PROMPT = """You are a Contradiction Detector. You are given a list of extracted factual claims from different sources.
Identify if there are any direct conflicts, discrepancies, or contradictions among these claims (e.g., conflicting dates, versions, figures, or support claims).
Format your output as a JSON list of dictionaries containing keys:
- "claim_a": The first claim
- "claim_b": The conflicting claim
- "reason": Why they contradict

If no contradictions are found, return an empty JSON list [].

Claims:
{claims_text}
"""

class FactExtractionEngine:
    @staticmethod
    def extract_facts(text: str, model: genai.GenerativeModel | None = None) -> list[str]:
        """
        Extracts discrete factual assertions from the source text.
        """
        if not text or not text.strip():
            return []
            
        if model:
            try:
                prompt = FACT_EXTRACTION_PROMPT.format(text=text)
                response = model.generate_content(prompt)
                res_text = response.text.strip()
                # Clean up json format if wrapped in backticks
                if "```json" in res_text:
                    res_text = res_text.split("```json")[1].split("```")[0].strip()
                elif "```" in res_text:
                    res_text = res_text.split("```")[1].split("```")[0].strip()
                
                import json
                claims = json.loads(res_text)
                if isinstance(claims, list):
                    return [str(c).strip() for c in claims]
            except Exception as e:
                logger.error(f"LLM fact extraction failed, falling back to heuristics: {e}")
                
        # Heuristic fallback (Sentence parsing & filtering)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        facts = []
        for s in sentences:
            s = s.strip()
            if len(s) < 20 or len(s) > 200:
                continue
            # Simple heuristic for fact-like sentences (e.g., contains verbs, nouns, numbers, or specific keywords)
            if any(k in s.lower() for k in ["is", "was", "are", "were", "released", "announced", "fixes", "supports", "new", "version", "deprecate", "update", "github"]):
                facts.append(s)
        return facts[:5] # Limit number of facts per snippet in fallback

class ContradictionDetectionEngine:
    @staticmethod
    def detect_contradictions(claims: list[str], model: genai.GenerativeModel | None = None) -> list[dict]:
        """
        Compares factual claims to identify conflicts.
        """
        if not claims or len(claims) < 2:
            return []
            
        if model:
            try:
                claims_text = "\n".join(f"- {c}" for c in claims)
                prompt = CONTRADICTION_DETECTION_PROMPT.format(claims_text=claims_text)
                response = model.generate_content(prompt)
                res_text = response.text.strip()
                if "```json" in res_text:
                    res_text = res_text.split("```json")[1].split("```")[0].strip()
                elif "```" in res_text:
                    res_text = res_text.split("```")[1].split("```")[0].strip()
                
                import json
                contradictions = json.loads(res_text)
                if isinstance(contradictions, list):
                    return contradictions
            except Exception as e:
                logger.error(f"LLM contradiction detection failed, falling back to heuristics: {e}")
                
        # Heuristic fallback: simple detection of conflicting numbers or negation terms in close sentences
        contradictions = []
        # Look for numeric conflicts on the same subject
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1 = claims[i].lower()
                c2 = claims[j].lower()
                # Find matching words except numbers and negations
                words1 = set(re.findall(r'\b\w+\b', c1))
                words2 = set(re.findall(r'\b\w+\b', c2))
                overlap = words1.intersection(words2)
                
                # If they share significant common words but differ on numbers/negations
                if len(overlap) > 3:
                    # Look for numerical discrepancies
                    nums1 = set(re.findall(r'\b\d+(?:\.\d+)?\b', c1))
                    nums2 = set(re.findall(r'\b\d+(?:\.\d+)?\b', c2))
                    if nums1 and nums2 and nums1 != nums2:
                        contradictions.append({
                            "claim_a": claims[i],
                            "claim_b": claims[j],
                            "reason": f"Discrepancy in numeric values: {nums1} vs {nums2}"
                        })
                    # Look for explicit negation conflicts (e.g. support vs not support)
                    elif ("no" in words1 or "not" in words1) != ("no" in words2 or "not" in words2):
                        if any(term in overlap for term in ["support", "work", "fix", "release", "compatible"]):
                            contradictions.append({
                                "claim_a": claims[i],
                                "claim_b": claims[j],
                                "reason": "Potential contradiction involving negation."
                            })
        return contradictions

class CitationGenerator:
    @staticmethod
    def format_citations(sources: list[dict]) -> tuple[dict[str, str], str]:
        """
        Creates a map of source URLs to footnote labels and formats a markdown sources index.
        """
        citation_map = {}
        for idx, src in enumerate(sources):
            url = src.get("href", "")
            if url:
                citation_map[url] = f"[^{idx + 1}]"
                
        # Format sources bibliography
        bibliography = "### Sources Consulted\n"
        for idx, src in enumerate(sources):
            title = src.get("title", f"Source {idx + 1}")
            url = src.get("href", "#")
            bibliography += f"[{idx + 1}] **{title}** - <{url}>\n"
            
        return citation_map, bibliography
