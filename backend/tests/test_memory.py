import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.memory.service import MemoryService

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        from backend.app.core.database import Memory
        db.query(Memory).filter(Memory.category.in_(["test_cat", "api_test_cat"])).delete(synchronize_session=False)
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
        from backend.app.core.database import Memory
        db.query(Memory).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield



def test_memory_crud_service(setup_db):
    db = SessionLocal()
    try:
        # 1. Create memory
        mem = MemoryService.create_or_update_memory(
            db=db,
            entity_key="test_key",
            entity_value="test_value",
            category="test_cat",
            salience_score=2.0
        )
        assert mem.id is not None
        assert mem.entity_key == "test_key"
        assert mem.entity_value == "test_value"
        
        # 2. List memories
        m_list = MemoryService.list_memories(db=db, category="test_cat")
        assert len(m_list) > 0
        assert any(m.entity_key == "test_key" for m in m_list)
        
        # 3. Retrieve/Search
        search_results = MemoryService.search_memories(db=db, query="test_key", limit=1)
        assert len(search_results) > 0
        assert "test_key" in search_results[0]["text"]
        
        # 4. Delete memory
        success = MemoryService.delete_memory(db=db, memory_id=mem.id)
        assert success is True
        
        # Verify deletion
        deleted_mem = MemoryService.get_memory_by_id(db=db, memory_id=mem.id)
        assert deleted_mem is None
    finally:
        db.close()

def test_memory_api_endpoints(setup_db):
    # 1. Store memory
    payload = {
        "key": "api_test_key",
        "value": "api_test_value",
        "category": "api_test_cat",
        "salience_score": 4.5
    }
    response = client.post("/api/memory/store", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    memory_id = data["memory_id"]
    assert memory_id is not None
    
    # 2. List memories
    response = client.get("/api/memory?category=api_test_cat")
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert items[0]["entity_key"] == "api_test_key"
    
    # 3. Retrieve memories semantically
    retrieve_payload = {
        "query": "api_test_key",
        "limit": 1
    }
    response = client.post("/api/memory/retrieve", json=retrieve_payload)
    assert response.status_code == 200
    results_data = response.json()
    assert len(results_data["results"]) > 0
    assert "api_test_key" in results_data["results"][0]["text"]
    
    # 4. Delete memory
    response = client.delete(f"/api/memory/{memory_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
