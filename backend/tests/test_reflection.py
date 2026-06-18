import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, Goal, Task, AttentionLog, KnowledgeNode, KnowledgeEdge, Memory, User
from backend.app.services.executive.reflection import ReflectionService
from backend.app.agents.reflection import ReflectionAgent

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup database
    db = SessionLocal()
    try:
        db.query(Task).delete()
        db.query(Goal).delete()
        db.query(AttentionLog).delete()
        db.query(KnowledgeEdge).delete()
        db.query(KnowledgeNode).delete()
        db.query(Memory).delete()
        db.query(User).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_reflection_data():
    db = SessionLocal()
    try:
        db.query(Task).delete()
        db.query(Goal).delete()
        db.query(AttentionLog).delete()
        db.query(KnowledgeEdge).delete()
        db.query(KnowledgeNode).delete()
        db.query(Memory).delete()
        db.query(User).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

def test_reflection_agent_generation():
    agent = ReflectionAgent()
    telemetry = {
        "date": "2026-06-18",
        "active_project": "JARVIS-gpt",
        "completed_tasks": [{"title": "Write unit tests", "description": "Verify RCE"}],
        "pending_tasks": [{"title": "Build Reflection Engine", "description": "Cycle 3"}],
        "focus_efficiency": 90.0,
        "attention_status": "aligned"
    }
    report = agent.generate_reflection_report(telemetry)
    assert "summary" in report
    assert "what_worked" in report
    assert "what_failed" in report
    assert "adjustments" in report

def test_reflection_service_generation(setup_db):
    db = SessionLocal()
    try:
        # 1. Setup mock user and project data
        user = User(username="reflect_user")
        db.add(user)
        db.commit()

        # Seed Goal that will be matched to adjust priorities
        goal = Goal(
            user_id=user.id,
            title="Implement Reflection Engine Subsystem",
            description="Build Cycle 3 self-improvement engine",
            status="in_progress",
            priority_weight=1.0
        )
        db.add(goal)
        db.commit()

        # Seed completed & pending tasks
        task_comp = Task(
            goal_id=goal.id,
            title="Write RCE code",
            status="completed",
            completed_at=datetime.utcnow()
        )
        task_pend = Task(
            goal_id=goal.id,
            title="Refactor Reflection script",
            status="pending"
        )
        db.add(task_comp)
        db.add(task_pend)
        db.commit()

        # Seed some attention logs
        log = AttentionLog(
            active_application="VS Code",
            active_window_title="reflection.py",
            time_spent_seconds=1200.0,
            category="coding",
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()

        # 2. Run Reflection generation
        res = ReflectionService.generate_reflection(db)
        assert res["node_id"].startswith("reflection_")
        assert "report" in res
        
        # 3. Assert KnowledgeNode was saved
        node = db.query(KnowledgeNode).filter(KnowledgeNode.id == res["node_id"]).first()
        assert node is not None
        assert node.node_type == "reflection"
        assert "summary" in node.properties

        # 4. Assert edge was created
        edge = db.query(KnowledgeEdge).filter(
            KnowledgeEdge.source_node_id == "user_me",
            KnowledgeEdge.relationship_type == "REFLECTED_ON",
            KnowledgeEdge.target_node_id == res["node_id"]
        ).first()
        assert edge is not None

        # 5. Assert memory insights saved
        mem = db.query(Memory).filter(Memory.category == "reflection").first()
        assert mem is not None
        assert mem.entity_key.startswith("reflection_insights_")

        # 6. Assert dynamic priorities adjustment was reinforced
        # The goal title "Implement Reflection Engine Subsystem" has words "reflection" and "engine"
        # which will be present in the generated/fallback report adjustments, triggering reinforcement
        db.refresh(goal)
        assert goal.priority_weight > 1.0

    finally:
        db.close()

def test_reflection_api_endpoints(setup_db):
    # Setup mock user and goal so service does not raise during POST
    db = SessionLocal()
    try:
        user = User(username="api_user")
        db.add(user)
        db.commit()
        goal = Goal(user_id=user.id, title="Reflect API goal", priority_weight=1.0)
        db.add(goal)
        db.commit()
    finally:
        db.close()

    # 1. Trigger manual reflection
    response = client.post("/api/executive/reflect")
    assert response.status_code == 200
    data = response.json()
    assert "node_id" in data
    assert "report" in data
    
    # 2. Get history list
    response = client.get("/api/executive/reflections?limit=5")
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0
    assert history[0]["id"] == data["node_id"]
    assert "summary" in history[0]["properties"]
