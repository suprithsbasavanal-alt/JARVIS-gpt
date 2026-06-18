import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, Goal, Task, Message, ActionAuditLog, KnowledgeNode, KnowledgeEdge, Memory, User
from backend.app.services.executive.critic import AgentCriticService
from backend.app.agents.critic import CriticAgent

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
        db.query(Message).delete()
        db.query(ActionAuditLog).delete()
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
def clean_critic_data():
    db = SessionLocal()
    try:
        db.query(Task).delete()
        db.query(Goal).delete()
        db.query(Message).delete()
        db.query(ActionAuditLog).delete()
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

def test_critic_agent_generation():
    agent = CriticAgent()
    metrics = {
        "date": "2026-06-18",
        "task_count": 5,
        "messages_count": 12,
        "audit_logs_count": 3,
        "safety_failures_count": 0
    }
    report = agent.evaluate_performance(metrics)
    assert "planning_grade" in report
    assert "planning_critique" in report
    assert "research_grade" in report
    assert "research_critique" in report
    assert "automation_grade" in report
    assert "automation_critique" in report
    assert "memory_grade" in report
    assert "memory_critique" in report
    assert "overall_feedback" in report

def test_critic_service_evaluation(setup_db):
    db = SessionLocal()
    try:
        # 1. Setup mock data
        user = User(username="critic_user")
        db.add(user)
        db.commit()

        # Seed goal and tasks
        goal = Goal(user_id=user.id, title="Test goal", priority_weight=1.0)
        db.add(goal)
        db.commit()

        task = Task(goal_id=goal.id, title="Test Task", status="completed", completed_at=datetime.utcnow())
        db.add(task)
        db.commit()

        # Seed ActionAuditLogs and messages
        audit = ActionAuditLog(action_type="shell_cmd", command_payload="ls", is_approved=True, created_at=datetime.utcnow())
        db.add(audit)
        db.commit()

        # 2. Run AgentCriticService evaluation
        res = AgentCriticService.evaluate_agent_performance(db)
        assert res["node_id"].startswith("evaluation_")
        assert "evaluation" in res
        
        # 3. Assert KnowledgeNode was saved
        node = db.query(KnowledgeNode).filter(KnowledgeNode.id == res["node_id"]).first()
        assert node is not None
        assert node.node_type == "evaluation"
        assert "planning_grade" in node.properties

        # 4. Assert edge was created
        edge = db.query(KnowledgeEdge).filter(
            KnowledgeEdge.source_node_id == "user_me",
            KnowledgeEdge.relationship_type == "EVALUATED_AGENTS",
            KnowledgeEdge.target_node_id == res["node_id"]
        ).first()
        assert edge is not None

    finally:
        db.close()

def test_critic_service_subpar_performance_memory(setup_db):
    db = SessionLocal()
    try:
        user = User(username="subpar_user")
        db.add(user)
        db.commit()

        # Seed safety gate intercept (unapproved audit log)
        audit_failed = ActionAuditLog(
            action_type="shell_cmd",
            command_payload="rm -rf /",
            is_approved=False,
            created_at=datetime.utcnow()
        )
        db.add(audit_failed)
        db.commit()

        # In mock mode, if safety_failures_count > 0, CriticAgent returns automation_grade = 6.0 (< 7.0)
        res = AgentCriticService.evaluate_agent_performance(db)
        assert res["evaluation"]["automation_grade"] < 7.0
        
        # Assert corrective critic memory is written
        mem = db.query(Memory).filter(Memory.category == "critic").first()
        assert mem is not None
        assert mem.entity_key.startswith("critic_feedback_")
        assert "Safety gates" in res["evaluation"]["automation_critique"]

    finally:
        db.close()

def test_critic_api_endpoints(setup_db):
    db = SessionLocal()
    try:
        user = User(username="api_critic_user")
        db.add(user)
        db.commit()
    finally:
        db.close()

    # 1. Trigger manual evaluation
    response = client.post("/api/executive/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert "node_id" in data
    assert "evaluation" in data
    
    # 2. Get history list
    response = client.get("/api/executive/evaluations?limit=5")
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0
    assert history[0]["id"] == data["node_id"]
    assert "planning_grade" in history[0]["properties"]
