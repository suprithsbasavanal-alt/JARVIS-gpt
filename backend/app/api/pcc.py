from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from backend.app.core.database import get_db
from backend.app.services.pcc.service import PCCService
from backend.app.services.pcc.consolidation import MemoryConsolidationService
from backend.app.services.pcc.cognitive_state import CognitiveStateService

router = APIRouter(prefix="/api/pcc", tags=["Personal Cognitive Core"])

# Schemas
class NodeUpsertRequest(BaseModel):
    id: str = Field(..., description="Unique node ID")
    type: str = Field(..., description="Node classification type, e.g. skill, project, goal")
    label: str = Field(..., description="Display label for the node")
    properties: dict | None = Field(None, description="Optional metadata properties")
    salience_score: float = Field(1.0, description="Salience weight, between 0.0 and 5.0")

class EdgeUpsertRequest(BaseModel):
    source_id: str = Field(..., description="Source node ID")
    relationship: str = Field(..., description="Type of relationship, e.g. REQUIRES, WORKS_ON")
    target_id: str = Field(..., description="Target node ID")
    weight: float = Field(1.0, description="Relationship strength weight")

class ContextRequest(BaseModel):
    active_focus: str = Field(..., description="Active task topic or query context to retrieve information for")
    limit: int = Field(5, ge=1, le=20)

class AttentionLogRequest(BaseModel):
    active_application: str = Field(..., description="Active program/app name")
    active_window_title: str = Field(..., description="Title of the active window")
    time_spent_seconds: float = Field(..., ge=0.1, description="Seconds spent in this view")
    category: str = Field("coding", description="Category classification, e.g. coding, distraction, research")

# Endpoints
@router.post("/nodes")
def upsert_node(request: NodeUpsertRequest, db: Session = Depends(get_db)):
    """
    Insert or update a node in the Personal Knowledge Graph.
    """
    try:
        node = PCCService.upsert_node(
            db=db,
            node_id=request.id,
            node_type=request.type,
            label=request.label,
            properties=request.properties,
            salience_score=request.salience_score
        )
        return {
            "status": "success",
            "node": {
                "id": node.id,
                "type": node.node_type,
                "label": node.label,
                "salience": float(node.salience_score)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upsert node: {str(e)}")

@router.post("/edges")
def upsert_edge(request: EdgeUpsertRequest, db: Session = Depends(get_db)):
    """
    Insert or update a relationship edge between two existing nodes.
    """
    try:
        edge = PCCService.upsert_edge(
            db=db,
            source_node_id=request.source_id,
            relationship_type=request.relationship,
            target_node_id=request.target_id,
            weight=request.weight
        )
        return {
            "status": "success",
            "edge": {
                "id": str(edge.id),
                "source": edge.source_node_id,
                "relationship": edge.relationship_type,
                "target": edge.target_node_id,
                "weight": float(edge.weight)
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upsert edge: {str(e)}")

@router.get("/traverse")
def traverse_graph(start_node_id: str, max_depth: int = 2, db: Session = Depends(get_db)):
    """
    Traverse adjacent connections starting from a specific node up to max_depth.
    """
    try:
        data = PCCService.traverse_graph(db=db, start_node_id=start_node_id, max_depth=max_depth)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph traversal failed: {str(e)}")

@router.post("/context")
def retrieve_cognitive_context(request: ContextRequest, db: Session = Depends(get_db)):
    """
    Retrieve unified context (RAG vector results + Knowledge Graph path structures) matching active focus.
    """
    try:
        data = PCCService.compile_cognitive_context(db=db, active_focus=request.active_focus, limit=request.limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context collection failed: {str(e)}")

@router.post("/consolidate")
def run_memory_consolidation(db: Session = Depends(get_db)):
    """
    Scan raw chat messages and synthesize new project/skill nodes and edges into the PKG.
    """
    try:
        summary = MemoryConsolidationService.consolidate_episodic_logs(db=db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consolidation loop failed: {str(e)}")

@router.get("/cognitive-state")
def get_cognitive_state(db: Session = Depends(get_db)):
    """
    Compute real-time focus category, cognitive load level, and attention drift warnings.
    """
    try:
        state = CognitiveStateService.get_active_cognitive_state(db=db)
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile focus state: {str(e)}")

@router.post("/attention")
def log_attention(request: AttentionLogRequest, db: Session = Depends(get_db)):
    """
    Record an attention activity slice (e.g. log window tracking metrics).
    """
    try:
        log = CognitiveStateService.log_attention_activity(
            db=db,
            active_application=request.active_application,
            active_window_title=request.active_window_title,
            time_spent_seconds=request.time_spent_seconds,
            category=request.category
        )
        return {"status": "success", "log_id": str(log.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save focus segment: {str(e)}")
