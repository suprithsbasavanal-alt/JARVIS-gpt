import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from backend.app.core.database import get_db
from backend.app.services.memory.service import MemoryService

router = APIRouter(prefix="/api/memory", tags=["Memory Fabric"])

# Schemas
class MemoryStoreRequest(BaseModel):
    key: str = Field(..., description="Unique semantic key for the memory")
    value: str = Field(..., description="Content of the memory")
    category: str = Field("general", description="Category classification, e.g. preference, lifestyle, project")
    salience_score: float = Field(1.0, description="Salience weight of this memory, between 0.0 and 5.0")

class MemoryStoreResponse(BaseModel):
    status: str
    memory_id: str

class MemoryRetrieveRequest(BaseModel):
    query: str = Field(..., description="Query phrase for semantic search")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of search results to return")

class SearchResultItem(BaseModel):
    text: str
    category: str | None = None
    score: float
    metadata: dict | None = None

class MemoryRetrieveResponse(BaseModel):
    results: list[SearchResultItem]

class MemoryItemResponse(BaseModel):
    id: str
    entity_key: str
    entity_value: str
    category: str | None
    salience_score: float
    created_at: str
    updated_at: str


@router.post("/store", response_model=MemoryStoreResponse)
def store_memory(request: MemoryStoreRequest, db: Session = Depends(get_db)):
    """
    Store or update a belief, preference, or habit in the relational database and vectorize to Qdrant.
    """
    try:
        db_memory = MemoryService.create_or_update_memory(
            db=db,
            entity_key=request.key,
            entity_value=request.value,
            category=request.category,
            salience_score=request.salience_score
        )
        return MemoryStoreResponse(status="success", memory_id=str(db_memory.id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")

@router.post("/retrieve", response_model=MemoryRetrieveResponse)
def retrieve_memories(request: MemoryRetrieveRequest, db: Session = Depends(get_db)):
    """
    Perform semantic vector lookup against Qdrant to find relevant memories.
    """
    try:
        raw_results = MemoryService.search_memories(db=db, query=request.query, limit=request.limit)
        results = []
        for r in raw_results:
            meta = r.get("metadata", {})
            results.append(SearchResultItem(
                text=r.get("text", ""),
                category=meta.get("category"),
                score=r.get("score", 0.0),
                metadata=meta
            ))
        return MemoryRetrieveResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")

@router.get("", response_model=list[MemoryItemResponse])
def list_memories(category: str | None = None, db: Session = Depends(get_db)):
    """
    List all stored memories in the relational database, optionally filtered by category.
    """
    try:
        db_memories = MemoryService.list_memories(db=db, category=category)
        return [
            MemoryItemResponse(
                id=str(m.id),
                entity_key=m.entity_key,
                entity_value=m.entity_value,
                category=m.category,
                salience_score=float(m.salience_score),
                created_at=m.created_at.isoformat(),
                updated_at=m.updated_at.isoformat()
            ) for m in db_memories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list memories: {str(e)}")

@router.delete("/{memory_id}")
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """
    Delete a specific memory by its unique database ID.
    """
    try:
        uuid_id = uuid.UUID(memory_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory UUID format")
        
    success = MemoryService.delete_memory(db=db, memory_id=uuid_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    return {"status": "success", "message": f"Memory {memory_id} deleted successfully."}
