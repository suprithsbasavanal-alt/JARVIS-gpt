import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, WorldEvent, Opportunity, Risk, Project, Goal, KnowledgeNode, KnowledgeEdge
from backend.app.services.world_model.ingestion import RSSIngestor, TrendFilter
from backend.app.services.world_model.relevance import RelevanceMatcher, StrategicAlertSystem
from backend.app.services.world_model.service import WorldModelService

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        db.query(WorldEvent).delete()
        db.query(Opportunity).delete()
        db.query(Risk).delete()
        db.query(Project).delete()
        db.query(Goal).delete()
        db.query(KnowledgeEdge).filter(KnowledgeEdge.relationship_type == "RELEVANT_EVENT").delete()
        db.query(KnowledgeNode).filter(KnowledgeNode.node_type == "world_event").delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_stores():
    db = SessionLocal()
    try:
        db.query(WorldEvent).delete()
        db.query(Opportunity).delete()
        db.query(Risk).delete()
        db.query(Project).delete()
        db.query(Goal).delete()
        db.query(KnowledgeEdge).filter(KnowledgeEdge.relationship_type == "RELEVANT_EVENT").delete()
        db.query(KnowledgeNode).filter(KnowledgeNode.node_type == "world_event").delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

def test_rss_ingestor_and_filter():
    items = RSSIngestor.fetch_and_parse("https://cve.mitre.org/mock-feed")
    assert len(items) >= 2
    assert "CVE-2026-9988" in items[0]["title"]
    
    cat1 = TrendFilter.classify_item(items[0]["title"], items[0]["description"])
    assert cat1 == "Security Vulnerability"
    
    ai_items = RSSIngestor.fetch_and_parse("https://hacker-news/mock-ai")
    cat2 = TrendFilter.classify_item(ai_items[0]["title"], ai_items[0]["description"])
    assert cat2 == "AI Release"

def test_relevance_matching(setup_db):
    db = SessionLocal()
    try:
        # No context -> low score
        score_none = RelevanceMatcher.score_relevance(db, "New release of FastAPI v1.0", "A new web framework version.")
        assert score_none <= 0.2
        
        # Seed context: Project using FastAPI
        proj = Project(name="Test Jarvis", workspace_path="/safe/path", technologies=["fastapi", "python"])
        db.add(proj)
        db.commit()
        
        # Match matches technologies list
        score = RelevanceMatcher.score_relevance(db, "Critical CVE detected in FastAPI", "FastAPI vulnerability details.")
        assert score >= 0.8
    finally:
        db.close()

def test_strategic_alert_system(setup_db):
    db = SessionLocal()
    try:
        # 1. Trigger Opportunity alert
        alert_opp = StrategicAlertSystem.process_and_alert(
            db=db,
            world_event_id=str(uuid.uuid4()),
            title="Qwen-3 LLM Released",
            description="A new state of the art open source model weights.",
            category="AI Release",
            relevance_score=0.85,
            source_url="https://github.com/qwen"
        )
        assert alert_opp is not None
        assert alert_opp["type"] == "opportunity"
        
        db_opp = db.query(Opportunity).filter(Opportunity.id == uuid.UUID(alert_opp["id"])).first()
        assert db_opp is not None
        assert db_opp.relevance_score == 0.85
        
        # 2. Trigger Risk alert
        alert_risk = StrategicAlertSystem.process_and_alert(
            db=db,
            world_event_id=str(uuid.uuid4()),
            title="CVE-2026-9988: Critical remote execution in FastAPI",
            description="Vulnerability body.",
            category="Security Vulnerability",
            relevance_score=0.9,
            source_url="https://nvd.nist.gov"
        )
        assert alert_risk is not None
        assert alert_risk["type"] == "risk"
        
        db_risk = db.query(Risk).filter(Risk.id == uuid.UUID(alert_risk["id"])).first()
        assert db_risk is not None
        assert db_risk.severity == "critical"
    finally:
        db.close()

def test_world_model_service_orchestration(setup_db):
    db = SessionLocal()
    try:
        # Seed Project to ensure some events are relevant (> 0.7) and trigger alerts/PKG syncs
        proj = Project(name="Jarvis Main", workspace_path="/safe/workspace", technologies=["fastapi", "python"])
        db.add(proj)
        db.commit()
        
        summary = WorldModelService.ingest_feeds(db)
        assert summary["status"] == "success"
        assert summary["events_ingested"] >= 3
        assert len(summary["alerts_triggered"]) >= 1
        
        # Verify World Event logged in database
        event = db.query(WorldEvent).first()
        assert event is not None
        
        # Verify PKG sync worked
        node = db.query(KnowledgeNode).filter(KnowledgeNode.node_type == "world_event").first()
        assert node is not None
        
        edge = db.query(KnowledgeEdge).filter(
            KnowledgeEdge.source_node_id == "user_me",
            KnowledgeEdge.relationship_type == "RELEVANT_EVENT",
            KnowledgeEdge.target_node_id == node.id
        ).first()
        assert edge is not None
    finally:
        db.close()

def test_world_model_api_endpoints(setup_db):
    db = SessionLocal()
    try:
        # Seed Project to ensure some events are relevant (> 0.7) and trigger alerts
        proj = Project(name="Jarvis Main", workspace_path="/safe/workspace", technologies=["fastapi", "python"])
        db.add(proj)
        db.commit()
    finally:
        db.close()

    # Trigger Ingestion Scrape
    response = client.post("/api/world-model/ingest", json={"feed_urls": None})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Query strategic alerts
    response = client.get("/api/world-model/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    
    # Query world events
    response = client.get("/api/world-model/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 3
