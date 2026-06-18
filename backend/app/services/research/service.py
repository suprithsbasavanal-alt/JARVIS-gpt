import logging
import uuid
import re
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.services.research.collector import MultiSourceCollector, DuplicateDetectionEngine
from backend.app.services.research.scorer import SourceCredibilityScorer, ConfidenceScoringEngine
from backend.app.services.research.verifier import FactExtractionEngine, ContradictionDetectionEngine, CitationGenerator
from backend.app.services.memory.service import MemoryService
from backend.app.services.pcc.service import PCCService

logger = logging.getLogger(__name__)

class ResearchService:
    @staticmethod
    def research_required(query: str) -> bool:
        """
        Determines if a query requires research (i.e. asks for external or latest info, vs simple talk).
        """
        query_lower = query.lower().strip()
        # Simple greetings or settings updates
        if any(g in query_lower for g in ["hello", "hi", "how are you", "who are you", "clear history", "show settings"]):
            return False
            
        # Common triggers for research queries
        research_indicators = [
            "what is", "who is", "latest", "recent", "news", "trend", "how to", "released", "announced",
            "vs", "compare", "benchmark", "error", "failed", "bug", "why does", "documentation"
        ]
        return any(ind in query_lower for ind in research_indicators)

    @staticmethod
    def perform_research(
        db: Session,
        topic: str,
        save_memory: bool = False,
        model = None
    ) -> dict:
        """
        Executes the Search -> Collect -> De-duplicate -> Score -> Verify -> Citations -> Memory flow.
        """
        logger.info(f"Starting research orchestrator for topic: '{topic}'")
        
        # 1. Collect raw sources
        raw_sources = MultiSourceCollector.collect_sources(topic)
        
        # 2. De-duplicate sources
        unique_sources = DuplicateDetectionEngine.remove_duplicates(raw_sources)
        
        if not unique_sources:
            return {
                "briefing": "No unique sources could be found or parsed for the topic.",
                "sources": [],
                "facts": [],
                "contradictions": [],
                "confidence_score": 0.0
            }
            
        # 3. Extract facts & compute domain credibilities
        all_claims = []
        source_details = []
        for src in unique_sources:
            title = src.get("title", "")
            url = src.get("href", "")
            body = src.get("body", "")
            
            credibility = SourceCredibilityScorer.score_source(url)
            source_details.append({
                "title": title,
                "href": url,
                "body": body,
                "credibility": credibility
            })
            
            # Extract claims from body
            claims = FactExtractionEngine.extract_facts(body, model=model)
            all_claims.extend(claims)
            
        # 4. Detect contradictions
        contradictions = ContradictionDetectionEngine.detect_contradictions(all_claims, model=model)
        
        # 5. Calculate Confidence Score
        confidence = ConfidenceScoringEngine.calculate_confidence(
            sources=source_details,
            contradiction_count=len(contradictions),
            total_claims_count=len(all_claims)
        )
        
        # 6. Citations & Bibliography
        citation_map, bibliography = CitationGenerator.format_citations(source_details)
        
        # 7. Synthesize briefing
        briefing = f"# Research Briefing: {topic}\n\n"
        
        # Executive Summary Heuristic / LLM response
        if model:
            try:
                sources_str = "\n".join(f"Source [{idx+1}]: {s['title']} ({s['href']})\nBody: {s['body']}" for idx, s in enumerate(source_details))
                summary_prompt = (
                    f"Create an executive summary and consolidated briefing in markdown for topic: '{topic}' "
                    f"using these sources:\n{sources_str}\n\nMake sure to add footnote citations like [^1], [^2] where appropriate."
                )
                response = model.generate_content(summary_prompt)
                briefing += response.text.strip() + "\n\n"
            except Exception as e:
                logger.error(f"Failed to generate briefing via LLM, falling back to heuristics: {e}")
                
        # Heuristic briefing construction
        if not model or "Research Briefing:" in briefing and len(briefing) < 50:
            briefing += "## Executive Summary\n"
            briefing += f"Consolidated analysis of {len(source_details)} unique sources. "
            briefing += "Information has been indexed and validated for consistency.\n\n"
            
            briefing += "## Consolidated Facts\n"
            for idx, claim in enumerate(all_claims[:10]):
                # Map claim to its source index footnote if possible
                footnote = ""
                for s_idx, src in enumerate(source_details):
                    if src["body"] and claim[:30].lower() in src["body"].lower():
                        footnote = f" [^{s_idx + 1}]"
                        break
                briefing += f"- {claim}{footnote}\n"
            briefing += "\n"
            
            if contradictions:
                briefing += "## Identified Contradictions & Discrepancies\n"
                for c in contradictions:
                    briefing += f"- **Conflict**: \"{c['claim_a']}\" **VS** \"{c['claim_b']}\"\n"
                    briefing += f"  *Reason*: {c['reason']}\n"
                briefing += "\n"
                
        briefing += f"## Research Validation\n"
        briefing += f"- **Confidence Rating**: `{confidence} / 1.0`\n"
        briefing += f"- **Sources Scored**: {len(source_details)}\n\n"
        briefing += bibliography
        
        # 8. Save memory / PKG if requested
        if save_memory:
            # Store in relational + vector memory fabric
            sanitized_key = "research_" + re.sub(r'[^a-zA-Z0-9_]', '_', topic.lower())[:50]
            MemoryService.create_or_update_memory(
                db=db,
                entity_key=sanitized_key,
                entity_value=briefing,
                category="research",
                salience_score=confidence * 5.0  # Scale confidence to salience up to 5.0
            )
            
            # Integrate with Personal Knowledge Graph (PCC)
            try:
                # Ensure anchor user node exists
                PCCService.upsert_node(db, "user_me", "user", "Owner Profile")
                
                # Add research node
                node_id = f"research_{sanitized_key}"
                PCCService.upsert_node(
                    db=db,
                    node_id=node_id,
                    node_type="research",
                    label=f"Research: {topic}",
                    properties={
                        "confidence": confidence,
                        "sources_count": len(source_details),
                        "contradictions_count": len(contradictions)
                    }
                )
                
                # Link user to research node
                PCCService.upsert_edge(
                    db=db,
                    source_node_id="user_me",
                    relationship_type="RESEARCHED",
                    target_node_id=node_id,
                    weight=confidence
                )
            except Exception as e:
                logger.error(f"Error storing research in PKG: {e}")
                
        return {
            "briefing": briefing,
            "sources": [{"title": s["title"], "href": s["href"], "credibility": s["credibility"]} for s in source_details],
            "facts": all_claims,
            "contradictions": contradictions,
            "confidence_score": confidence
        }
