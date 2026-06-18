import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, Goal, Task, Opportunity, Risk, AttentionLog
from backend.app.services.executive import ExecutiveService, AttentionAllocationEngine, BriefingGenerator

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        db.query(Task).delete()
        db.query(Goal).delete()
        db.query(Opportunity).delete()
        db.query(Risk).delete()
        db.query(AttentionLog).delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_stores():
    db = SessionLocal()
    try:
        db.query(Task).delete()
        db.query(Goal).delete()
        db.query(Opportunity).delete()
        db.query(Risk).delete()
        db.query(AttentionLog).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

def test_priority_engine(setup_db):
    db = SessionLocal()
    try:
        # Create Goal
        g = Goal(title="Goal 1", priority_weight=2.0)
        db.add(g)
        db.commit()
        db.refresh(g)
        
        # Create Task with critical deadline
        t1 = Task(
            goal_id=g.id,
            title="Urgent task",
            status="pending",
            due_date=datetime.utcnow() + timedelta(hours=6)
        )
        
        # Create Task with distant deadline
        t2 = Task(
            goal_id=g.id,
            title="Relaxed task",
            status="pending",
            due_date=datetime.utcnow() + timedelta(days=5)
        )
        
        db.add_all([t1, t2])
        db.commit()
        
        priorities = ExecutiveService.get_most_important_tasks(db, limit=2)
        assert len(priorities) == 2
        assert priorities[0]["title"] == "Urgent task"
        assert priorities[0]["priority_score"] > priorities[1]["priority_score"]
    finally:
        db.close()

def test_goal_progress_alerts(setup_db):
    db = SessionLocal()
    try:
        # 1. Overdue Goal
        g = Goal(
            title="Overdue Goal",
            status="pending",
            target_deadline=datetime.utcnow() - timedelta(days=1)
        )
        db.add(g)
        db.commit()
        
        alerts = ExecutiveService.get_goals_behind_schedule(db)
        assert len(alerts) == 1
        assert alerts[0]["title"] == "Overdue Goal"
    finally:
        db.close()

def test_opportunity_and_risk_engines(setup_db):
    db = SessionLocal()
    try:
        # Register Opportunity
        opp = ExecutiveService.add_opportunity(db, "New Job", "AI Engineer", 4.5)
        assert opp.id is not None
        
        opps = ExecutiveService.get_active_opportunities(db)
        assert len(opps) == 1
        assert opps[0].title == "New Job"
        
        # Register Risk
        risk = ExecutiveService.add_risk(db, "System Failure", "Storage full", "critical", 0.9)
        assert risk.id is not None
        
        risks = ExecutiveService.get_active_risks(db)
        assert len(risks) == 1
        assert risks[0].title == "System Failure"
    finally:
        db.close()

def test_attention_allocation_engine(setup_db):
    db = SessionLocal()
    try:
        # Seed Attention logs
        AttentionAllocationEngine.get_attention_summary(db)
        
        log1 = AttentionLog(
            active_application="VS Code",
            active_window_title="main.py",
            time_spent_seconds=300.0,
            category="coding",
            timestamp=datetime.utcnow()
        )
        log2 = AttentionLog(
            active_application="Chrome",
            active_window_title="YouTube",
            time_spent_seconds=600.0,
            category="distraction",
            timestamp=datetime.utcnow()
        )
        db.add_all([log1, log2])
        db.commit()
        
        summary = AttentionAllocationEngine.get_attention_summary(db)
        assert summary["total_logged_minutes"] == 15.0
        assert summary["allocation_alignment_status"] == "distracted/scattered"
    finally:
        db.close()

def test_briefing_generators(setup_db):
    db = SessionLocal()
    try:
        # Just verify daily briefing and weekly review generate successfully without erroring
        db_brief = BriefingGenerator.generate_daily_briefing(db)
        assert "JARVIS Daily Strategic Briefing" in db_brief
        
        db_review = BriefingGenerator.generate_weekly_review(db)
        assert "JARVIS Weekly Retrospective Review" in db_review
    finally:
        db.close()

def test_executive_api_endpoints(setup_db):
    # 1. API Add Opportunity
    payload = {
        "title": "API Opp",
        "description": "API Test",
        "relevance_score": 4.8
    }
    response = client.post("/api/executive/opportunities", json=payload)
    assert response.status_code == 200
    
    # 2. API Add Risk
    risk_payload = {
        "title": "API Risk",
        "description": "API Test Risk",
        "severity": "high",
        "probability": 0.8
    }
    response = client.post("/api/executive/risks", json=risk_payload)
    assert response.status_code == 200
    
    # 3. API Daily Briefing
    response = client.get("/api/executive/briefing/daily")
    assert response.status_code == 200
    assert "briefing" in response.json()
    
    # 4. API Weekly Review
    response = client.get("/api/executive/briefing/weekly")
    assert response.status_code == 200
    assert "review" in response.json()
    
    # 5. API Priorities list
    response = client.get("/api/executive/priorities")
    assert response.status_code == 200
    assert "priorities" in response.json()
