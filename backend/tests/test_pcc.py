import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine, KnowledgeNode
from backend.app.services.pcc.service import PCCService
from backend.app.services.pcc.consolidation import MemoryConsolidationService
from backend.app.services.pcc.cognitive_state import CognitiveStateService

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test rows
    db = SessionLocal()
    try:
        from backend.app.core.database import KnowledgeNode, KnowledgeEdge, AttentionLog, Message, EventStore
        db.query(KnowledgeEdge).delete()
        db.query(KnowledgeNode).delete()
        db.query(AttentionLog).delete()
        db.query(Message).delete()
        db.query(EventStore).delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_graph_and_memory_stores():
    # Clear Qdrant mock
    from backend.app.services.memory import memory_store
    memory_store.clear()
    
    # Clear relational PCC structures
    db = SessionLocal()
    try:
        from backend.app.core.database import KnowledgeEdge, KnowledgeNode, AttentionLog, Message, EventStore
        db.query(KnowledgeEdge).delete()
        db.query(KnowledgeNode).delete()
        db.query(AttentionLog).delete()
        db.query(Message).delete()
        db.query(EventStore).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield

def test_pkg_node_and_edge_operations(setup_db):
    db = SessionLocal()
    try:
        # 1. Create source and target nodes
        n1 = PCCService.upsert_node(db, "node_one", "goal", "Finish JARVIS Project")
        n2 = PCCService.upsert_node(db, "node_two", "skill", "Python Programming")
        
        assert n1.id == "node_one"
        assert n2.id == "node_two"
        
        # 2. Create edge linking them
        edge = PCCService.upsert_edge(db, "node_one", "REQUIRES", "node_two", weight=2.0)
        assert edge.source_node_id == "node_one"
        assert edge.target_node_id == "node_two"
        assert float(edge.weight) == 2.0
        
        # 3. Retrieve adjacent nodes
        related = PCCService.get_related_nodes(db, "node_one")
        assert len(related) > 0
        assert related[0]["node"]["id"] == "node_two"
        
        # 4. Traversal
        traversed = PCCService.traverse_graph(db, "node_one", max_depth=1)
        assert len(traversed["nodes"]) == 2
        assert len(traversed["edges"]) == 2

    finally:
        db.close()

def test_cognitive_context_retrieval(setup_db):
    db = SessionLocal()
    try:
        # Create a project node
        PCCService.upsert_node(db, "proj_rust", "project", "Rust OS")
        # Compile context for 'rust'
        ctx = PCCService.compile_cognitive_context(db, active_focus="rust")
        assert ctx["active_focus"] == "rust"
        assert len(ctx["knowledge_graph"]["nodes"]) > 0
        assert ctx["knowledge_graph"]["nodes"][0]["id"] == "proj_rust"
    finally:
        db.close()

def test_memory_consolidation_service(setup_db):
    db = SessionLocal()
    try:
        # Seed an episodic message
        from backend.app.core.database import Message
        msg = Message(
            conversation_id=None,
            sender="user",
            content="I am working on jarvis and writing python code."
        )
        # We need a dummy conversation first since message requires it (or ForeignKey constraint)
        # Note: message conversation_id nullable?
        # In our database schema conversation_id is ForeignKey conversations.id nullable=False
        from backend.app.core.database import Conversation
        conv = Conversation(title="Test Conv")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        
        msg.conversation_id = conv.id
        db.add(msg)
        db.commit()
        
        # Run consolidation
        summary = MemoryConsolidationService.consolidate_episodic_logs(db)
        assert summary["status"] == "success"
        assert summary["nodes_added"] > 0
        
        # Verify node got created in PKG
        node = db.query(KnowledgeNode).filter(KnowledgeNode.id == "project_jarvis").first()
        assert node is not None
    finally:
        db.close()

def test_cognitive_state_attention_logs(setup_db):
    db = SessionLocal()
    try:
        # Log coding segment
        CognitiveStateService.log_attention_activity(
            db=db,
            active_application="VS Code",
            active_window_title="project_jarvis - main.py",
            time_spent_seconds=120.0,
            category="coding"
        )
        
        # Fetch active state
        state = CognitiveStateService.get_active_cognitive_state(db)
        assert state["active_application"] == "VS Code"
        assert "deep flow" in state["cognitive_load"] or "normal" in state["cognitive_load"]
    finally:
        db.close()

def test_pcc_api_endpoints(setup_db):
    # 1. API Node Upsert
    node_payload = {
        "id": "api_n1",
        "type": "skill",
        "label": "Rust Language",
        "properties": {"level": "expert"},
        "salience_score": 4.0
    }
    response = client.post("/api/pcc/nodes", json=node_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    node_payload2 = {
        "id": "api_n2",
        "type": "project",
        "label": "Compiler Build",
        "salience_score": 3.0
    }
    response = client.post("/api/pcc/nodes", json=node_payload2)
    assert response.status_code == 200
    
    # 2. API Edge Upsert
    edge_payload = {
        "source_id": "api_n2",
        "relationship": "REQUIRES",
        "target_id": "api_n1",
        "weight": 1.5
    }
    response = client.post("/api/pcc/edges", json=edge_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 3. API Traverse
    response = client.get("/api/pcc/traverse?start_node_id=api_n2&max_depth=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    
    # 4. API Attention Log
    att_payload = {
        "active_application": "Terminal",
        "active_window_title": "cargo build",
        "time_spent_seconds": 60.0,
        "category": "coding"
    }
    response = client.post("/api/pcc/attention", json=att_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 5. API Cognitive State
    response = client.get("/api/pcc/cognitive-state")
    assert response.status_code == 200
    state = response.json()
    assert state["active_application"] == "Terminal"
