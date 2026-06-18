import re
import logging

logger = logging.getLogger(__name__)

class IdentityExtractor:
    """
    Parses natural language conversation inputs to extract core user values, preferences, 
    motivations, learning styles, and future-self aspirations.
    """
    
    @staticmethod
    def extract_from_text(text: str) -> list[dict]:
        """
        Scan text using heuristic rules to extract identity markers.
        Returns a list of dicts: [{"key": str, "value": str, "category": str, "score": float}]
        """
        extracted = []
        clean_text = text.strip().rstrip(".?!")
        lower_text = clean_text.lower()
        
        # 1. Preferences Heuristics (e.g., "I prefer local AI over cloud AI")
        pref_patterns = [
            r"i prefer\s+([^.?!]+?)(?:\s+over\s+([^.?!]+))?$",
            r"my preference is\s+([^.?!]+)",
            r"i like\s+([^.?!]+?)\s+better than\s+([^.?!]+)",
            r"i favor\s+([^.?!]+)"
        ]
        for pattern in pref_patterns:
            match = re.search(pattern, lower_text)
            if match:
                val = match.group(1).strip()
                # Clean up connecting words
                key_base = val.replace(" ", "_")
                extracted.append({
                    "key": f"preference_{key_base}",
                    "value": clean_text[match.start(1):match.end(1)].strip(),
                    "category": "preference",
                    "score": 1.0
                })
                break
                
        # 2. Values Heuristics (e.g., "I value data privacy")
        value_patterns = [
            r"i value\s+([^.?!]+)",
            r"([^.?!]+?)\s+is (?:very )?important to me",
            r"my core value is\s+([^.?!]+)"
        ]
        for pattern in value_patterns:
            match = re.search(pattern, lower_text)
            if match:
                val = match.group(1).strip()
                key_base = val.replace(" ", "_")
                extracted.append({
                    "key": f"value_{key_base}",
                    "value": clean_text[match.start(1):match.end(1)].strip(),
                    "category": "value",
                    "score": 1.0
                })
                break

        # 3. Motivations Heuristics (e.g., "I am motivated by building local systems")
        mot_patterns = [
            r"i am motivated by\s+([^.?!]+)",
            r"my motivation is\s+([^.?!]+)",
            r"i want to\s+([^.?!]+?)\s+because\s+([^.?!]+)"
        ]
        for pattern in mot_patterns:
            match = re.search(pattern, lower_text)
            if match:
                val = match.group(1).strip()
                key_base = val.replace(" ", "_")[:30]
                extracted.append({
                    "key": f"motivation_{key_base}",
                    "value": clean_text[match.start(1):match.end(1)].strip(),
                    "category": "motivation",
                    "score": 1.0
                })
                break

        # 4. Learning Style Heuristics (e.g., "I learn best by hands-on building")
        learn_patterns = [
            r"i learn best by\s+([^.?!]+)",
            r"my learning style is\s+([^.?!]+)",
            r"i prefer learning through\s+([^.?!]+)"
        ]
        for pattern in learn_patterns:
            match = re.search(pattern, lower_text)
            if match:
                val = match.group(1).strip()
                key_base = val.replace(" ", "_")
                extracted.append({
                    "key": f"learning_style_{key_base}",
                    "value": clean_text[match.start(1):match.end(1)].strip(),
                    "category": "learning_style",
                    "score": 1.0
                })
                break

        # 5. Future Self Heuristics (e.g., "I want to become a principal AI engineer")
        future_patterns = [
            r"i want to become\s+a?s?\s*([^.?!]+)",
            r"my future self is\s+([^.?!]+)",
            r"i aspire to\s+([^.?!]+)"
        ]
        for pattern in future_patterns:
            match = re.search(pattern, lower_text)
            if match:
                val = match.group(1).strip()
                key_base = val.replace(" ", "_")
                extracted.append({
                    "key": f"future_self_{key_base}",
                    "value": clean_text[match.start(1):match.end(1)].strip(),
                    "category": "future_self",
                    "score": 1.0
                })
                break
                
        return extracted
