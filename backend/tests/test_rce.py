import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.executive.rce import ResponseClassifier
from backend.app.services.executive.router import CognitiveRouter
from backend.app.core.cache import cache

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # No extensive database cleanup needed as tests do not modify persistent schema state

@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield

def test_response_classifier_paths():
    # Path 1: Instant Response
    res = ResponseClassifier.classify("hi")
    assert res["path"] == 1
    assert res["target_latency"] == "< 1s"
    
    res = ResponseClassifier.classify("open Safari")
    assert res["path"] == 1
    
    res = ResponseClassifier.classify("what time is it?")
    assert res["path"] == 1

    # Path 4: Research Mode
    res = ResponseClassifier.classify("latest news about LLMs")
    assert res["path"] == 4
    assert res["target_latency"] == "< 60s"
    
    res = ResponseClassifier.classify("vulnerability CVE-2026-1234")
    assert res["path"] == 4

    # Path 2: Fast Response
    res = ResponseClassifier.classify("summarize this file")
    assert res["path"] == 2
    assert res["target_latency"] == "< 5s"
    
    res = ResponseClassifier.classify("show my active goals")
    assert res["path"] == 2

    # Path 3: Deep Thinking
    res = ResponseClassifier.classify("design a database schema for e-commerce")
    assert res["path"] == 3
    assert res["target_latency"] == "< 20s"

def test_cognitive_router_execution(setup_db):
    db = SessionLocal()
    try:
        # Path 1 (Instant)
        is_fast, reply, plan, path = CognitiveRouter.evaluate_path("hi", db)
        assert is_fast is True
        assert path == 1
        assert "JARVIS" in reply
        
        # Caching check
        # The next call with the same message should hit the cache
        is_fast_cached, reply_cached, plan_cached, path_cached = CognitiveRouter.evaluate_path("hi", db)
        assert is_fast_cached is True
        assert path_cached == 1
        assert reply_cached == reply
        
        # Path 2 (Fast)
        is_fast, reply, plan, path = CognitiveRouter.evaluate_path("summarize file", db)
        assert is_fast is True
        assert path == 2
        assert "Summary Mode" in reply
        
        # Path 3 & 4 (Should return False as they require background execution / planner loops)
        is_fast, reply, plan, path = CognitiveRouter.evaluate_path("compare rust vs python", db)
        assert is_fast is False
        assert path == 3
        
        is_fast, reply, plan, path = CognitiveRouter.evaluate_path("latest CVE security advisory", db)
        assert is_fast is False
        assert path == 4
    finally:
        db.close()

def test_chat_message_endpoint_routing(setup_db):
    # Test path 1 (Instant) endpoint response
    payload = {
        "message": "hello",
        "conversation_id": None
    }
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "conversation_id" in data
    assert "reply" in data
    assert "plan" in data
    
    # Test path 4 (Research Mode) endpoint response
    # It should return immediate processing status and kick off background task
    payload = {
        "message": "latest CVE news for FastAPI",
        "conversation_id": data["conversation_id"]
    }
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200
    data_processing = response.json()
    assert data_processing["status"] == "processing"
    assert "I am researching this" in data_processing["reply"]
