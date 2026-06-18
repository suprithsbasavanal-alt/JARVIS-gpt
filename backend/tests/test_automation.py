import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, AuditLog
from backend.app.services.automation.registry import ToolRegistry
from backend.app.services.automation.executor import FileManager, TerminalController
from backend.app.services.automation.safety import SafetyGate, AuditSystem
from backend.app.services.automation.service import AutomationService

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_stores():
    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

def test_tool_registry():
    tools = ToolRegistry.get_tool_schemas()
    assert len(tools) > 5
    assert ToolRegistry.get_tool("read_file") is not None
    assert ToolRegistry.get_tool("nonexistent") is None

def test_file_manager_safety():
    assert FileManager.is_safe_path("/Users/suprith.s.basavanal/Documents/antigrativity /JARVIS-gpt/main.py") is True
    assert FileManager.is_safe_path("/etc/passwd") is False

def test_safety_gate_evaluation():
    # Test safe path
    is_high, reason = SafetyGate.evaluate_risk("read_file", {"file_path": "/Users/suprith.s.basavanal/Documents/antigrativity /JARVIS-gpt/main.py"})
    assert not is_high
    
    # Test unsafe path
    is_high, reason = SafetyGate.evaluate_risk("read_file", {"file_path": "/etc/passwd"})
    assert is_high
    assert "outside the safe workspace" in reason
    
    # Test safe terminal cmd
    is_high, reason = SafetyGate.evaluate_risk("terminal_cmd", {"command": "git status"})
    assert not is_high
    
    # Test unsafe terminal cmd
    is_high, reason = SafetyGate.evaluate_risk("terminal_cmd", {"command": "rm -rf /"})
    assert is_high
    assert "matches dangerous pattern" in reason

def test_audit_system(setup_db):
    db = SessionLocal()
    try:
        log = AuditSystem.log_action(db, "terminal_cmd", "git status", is_approved=False)
        assert log.id is not None
        assert not log.is_approved
        
        pending = AuditSystem.get_pending_audits(db)
        assert len(pending) == 1
        assert pending[0].id == log.id
        
        approved_log = AuditSystem.approve_audit(db, log.id)
        assert approved_log.is_approved
        assert approved_log.approved_at is not None
    finally:
        db.close()

def test_automation_service_flow(setup_db):
    db = SessionLocal()
    try:
        # Create safe file test
        test_file = "/Users/suprith.s.basavanal/Documents/antigrativity /JARVIS-gpt/backend/tests/test_write.txt"
        res = AutomationService.execute_action(
            db=db,
            tool_name="create_file",
            arguments={"file_path": test_file, "content": "automation test line"}
        )
        assert res["status"] == "success"
        
        # Verify content
        read_res = AutomationService.execute_action(
            db=db,
            tool_name="read_file",
            arguments={"file_path": test_file}
        )
        assert read_res["status"] == "success"
        assert read_res["output"] == "automation test line"
        
        # Clean up file
        if os.path.exists(test_file):
            os.remove(test_file)
            
        # Trigger dangerous command -> expect blocked
        res_danger = AutomationService.execute_action(
            db=db,
            tool_name="terminal_cmd",
            arguments={"command": "rm -rf tmp"}
        )
        assert res_danger["status"] == "pending_approval"
        assert "audit_id" in res_danger
        
        # Approve and execute blocked command
        audit_id = uuid.UUID(res_danger["audit_id"])
        res_approved = AutomationService.execute_pending_action(db, audit_id)
        assert res_approved["status"] == "success"
    finally:
        db.close()

def test_automation_api_endpoints(setup_db):
    # Safe action execute
    payload = {
        "tool_name": "list_dir",
        "arguments": {"directory_path": "/Users/suprith.s.basavanal/Documents/antigrativity /JARVIS-gpt"}
    }
    response = client.post("/api/automation/execute", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Dangerous action execute -> expect pending
    danger_payload = {
        "tool_name": "terminal_cmd",
        "arguments": {"command": "sudo systemctl stop docker"}
    }
    response = client.post("/api/automation/execute", json=danger_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_approval"
    audit_id = data["audit_id"]
    
    # Get audits
    response = client.get("/api/automation/audit")
    assert response.status_code == 200
    audits = response.json()
    assert len(audits) >= 2
    
    # Approve and run
    response = client.post(f"/api/automation/approve/{audit_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
