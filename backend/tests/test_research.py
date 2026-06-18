import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, Memory, KnowledgeNode, KnowledgeEdge
from backend.app.services.research.collector import MultiSourceCollector, DuplicateDetectionEngine
from backend.app.services.research.scorer import SourceCredibilityScorer, ConfidenceScoringEngine
from backend.app.services.research.verifier import FactExtractionEngine, ContradictionDetectionEngine, CitationGenerator
from backend.app.services.research.service import ResearchService

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        db.query(Memory).filter(Memory.category == "research").delete()
        db.query(KnowledgeEdge).filter(KnowledgeEdge.relationship_type == "RESEARCHED").delete()
        db.query(KnowledgeNode).filter(KnowledgeNode.node_type == "research").delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_stores():
    db = SessionLocal()
    try:
        db.query(Memory).filter(Memory.category == "research").delete()
        db.query(KnowledgeEdge).filter(KnowledgeEdge.relationship_type == "RESEARCHED").delete()
        db.query(KnowledgeNode).filter(KnowledgeNode.node_type == "research").delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

def test_collector_and_deduplicator():
    raw = [
        {"title": "Python 3.13 News", "href": "https://wikipedia.org/wiki/python", "body": "Python 3.13 is finally here with JIT."},
        {"title": "Python 3.13 Wiki", "href": "https://wikipedia.org/wiki/python/", "body": "Python 3.13 is finally here with JIT."},
        {"title": "Random Blog", "href": "https://blog.example.com", "body": "This is just some unrelated blog post text."}
    ]
    deduped = DuplicateDetectionEngine.remove_duplicates(raw)
    assert len(deduped) == 2 # The second wikipedia link is a duplicate of the first
    assert deduped[0]["title"] == "Python 3.13 News"
    assert deduped[1]["title"] == "Random Blog"

def test_source_credibility_scorer():
    assert SourceCredibilityScorer.score_source("https://wikipedia.org/wiki/python") == 1.0
    assert SourceCredibilityScorer.score_source("https://blog.medium.com/post") == 0.75
    assert SourceCredibilityScorer.score_source("https://random-ad-site.biz/product") == 0.5

def test_confidence_scoring_engine():
    sources = [
        {"href": "https://wikipedia.org/wiki/python"},
        {"href": "https://docs.python.org/3"}
    ]
    # High credibility, no contradictions
    conf = ConfidenceScoringEngine.calculate_confidence(sources, 0, 5)
    assert conf > 0.6
    
    # Contradictions present -> penalty
    conf_penalty = ConfidenceScoringEngine.calculate_confidence(sources, 2, 5)
    assert conf_penalty < conf

def test_fact_extraction_and_contradiction():
    text = "Python 3.13 was released on October 7, 2024. It introduces a JIT compiler."
    facts = FactExtractionEngine.extract_facts(text)
    assert len(facts) > 0
    assert any("released" in f or "jit" in f.lower() for f in facts)
    
    claims = [
        "Python 3.13 release date is October 7, 2024.",
        "Python 3.13 release date is October 10, 2025."
    ]
    contradictions = ContradictionDetectionEngine.detect_contradictions(claims)
    assert len(contradictions) == 1
    assert "Discrepancy in numeric values" in contradictions[0]["reason"]

def test_citation_generator():
    sources = [
        {"title": "Wikipedia", "href": "https://wikipedia.org"}
    ]
    citation_map, bib = CitationGenerator.format_citations(sources)
    assert citation_map["https://wikipedia.org"] == "[^1]"
    assert "[1] **Wikipedia**" in bib

def test_research_service_orchestration(setup_db):
    db = SessionLocal()
    try:
        # Check topic trigger
        assert ResearchService.research_required("What is the latest Python 3.13 release date?") is True
        assert ResearchService.research_required("hello jarvis") is False
        
        # Run research orchestration and save to memory/graph
        res = ResearchService.perform_research(db, "Python 3.13 features", save_memory=True)
        assert "briefing" in res
        assert "confidence_score" in res
        assert len(res["sources"]) > 0
        
        # Verify stored in database memory
        stored_mem = db.query(Memory).filter(Memory.category == "research").first()
        assert stored_mem is not None
        assert "Research Briefing" in stored_mem.entity_value
        
        # Verify stored in graph
        stored_node = db.query(KnowledgeNode).filter(KnowledgeNode.node_type == "research").first()
        assert stored_node is not None
        assert "Research: Python 3.13 features" in stored_node.label
        
        stored_edge = db.query(KnowledgeEdge).filter(
            KnowledgeEdge.source_node_id == "user_me",
            KnowledgeEdge.relationship_type == "RESEARCHED",
            KnowledgeEdge.target_node_id == stored_node.id
        ).first()
        assert stored_edge is not None
    finally:
        db.close()

def test_research_api_endpoints(setup_db):
    payload = {
        "topic": "Python 3.13 release details",
        "save_memory": True
    }
    response = client.post("/api/research/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "briefing" in data
    assert "sources" in data
    assert "facts" in data
    assert "contradictions" in data
    assert "confidence_score" in data
