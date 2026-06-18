import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.identity.service import IdentityService

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        from backend.app.core.database import Memory, EventStore
        db.query(Memory).filter(Memory.category.in_(["value", "preference", "motivation", "learning_style", "future_self"])).delete(synchronize_session=False)
        db.query(EventStore).filter(EventStore.event_type.in_(["identity_created", "identity_updated"])).delete(synchronize_session=False)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_memory_store():
    from backend.app.services.memory import memory_store
    memory_store.clear()
    db = SessionLocal()
    try:
        from backend.app.core.database import Memory, EventStore
        db.query(Memory).delete(synchronize_session=False)
        db.query(EventStore).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield


def test_identity_extraction_heuristics():
    # 1. Preferences
    res = IdentityService.extract_and_integrate_from_text(db=SessionLocal(), text="I prefer local AI over cloud AI.")
    assert len(res) > 0
    assert res[0]["category"] == "preference"
    assert "local_ai" in res[0]["key"]
    
    # 2. Values
    res = IdentityService.extract_and_integrate_from_text(db=SessionLocal(), text="I value absolute data privacy.")
    assert len(res) > 0
    assert res[0]["category"] == "value"
    assert "data_privacy" in res[0]["key"]

    # 3. Motivation
    res = IdentityService.extract_and_integrate_from_text(db=SessionLocal(), text="I am motivated by building local systems.")
    assert len(res) > 0
    assert res[0]["category"] == "motivation"
    assert "building_local" in res[0]["key"]

    # 4. Learning style
    res = IdentityService.extract_and_integrate_from_text(db=SessionLocal(), text="I learn best by hands-on building.")
    assert len(res) > 0
    assert res[0]["category"] == "learning_style"
    assert "hands-on" in res[0]["key"]

    # 5. Future self
    res = IdentityService.extract_and_integrate_from_text(db=SessionLocal(), text="I want to become a principal AI engineer.")
    assert len(res) > 0
    assert res[0]["category"] == "future_self"
    assert "principal_ai_engineer" in res[0]["key"]

def test_identity_reinforcement_scoring(setup_db):
    db = SessionLocal()
    try:
        # First save starts at score 1.0
        db_item = IdentityService.reinforce_or_store_identity_item(
            db=db,
            key="preference_test_item",
            value="some value",
            category="preference",
            score_increment=0.5
        )
        assert float(db_item.salience_score) == 1.0
        
        # Second save increases score by 0.5
        db_item2 = IdentityService.reinforce_or_store_identity_item(
            db=db,
            key="preference_test_item",
            value="some value",
            category="preference",
            score_increment=0.5
        )
        assert float(db_item2.salience_score) == 1.5
    finally:
        db.close()

def test_identity_api_endpoints(setup_db):
    # 1. API Extract & Integrate
    payload = {"text": "I prefer local AI over cloud AI."}
    response = client.post("/api/identity/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["extracted"]) > 0
    assert data["extracted"][0]["category"] == "preference"
    
    # 2. API Reinforce
    reinforce_payload = {
        "key": "preference_local_ai",
        "value": "local AI over cloud AI",
        "category": "preference",
        "score_increment": 0.5
    }
    response = client.post("/api/identity/reinforce", json=reinforce_payload)
    assert response.status_code == 200
    r_data = response.json()
    assert r_data["status"] == "success"
    # Score should have evolved to 1.5 since the extraction prior already created it with 1.0
    assert r_data["new_score"] == 1.5
    
    # 3. API Profile Fetch
    response = client.get("/api/identity/profile")
    assert response.status_code == 200
    profile = response.json()
    assert "preference" in profile
    assert "preference_local_ai" in profile["preference"]
    assert profile["preference"]["preference_local_ai"]["value"] == "local AI over cloud AI"
