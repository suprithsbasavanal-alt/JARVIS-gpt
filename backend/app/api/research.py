import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.research.service import ResearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["Research & Verification"])

class ResearchRequest(BaseModel):
    topic: str
    save_memory: bool = False

class SourceDetail(BaseModel):
    title: str
    href: str
    credibility: float

class ContradictionDetail(BaseModel):
    claim_a: str
    claim_b: str
    reason: str

class ResearchResponse(BaseModel):
    briefing: str
    sources: list[SourceDetail]
    facts: list[str]
    contradictions: list[ContradictionDetail]
    confidence_score: float

@router.post("/query", response_model=ResearchResponse)
def run_research(payload: ResearchRequest, db: Session = Depends(get_db)):
    """
    Executes the multi-source research collector, scores credibility, de-duplicates hits,
    checks contradictions, scores confidence, and returns/saves the finalized briefing.
    """
    logger.info(f"API run_research invoked for topic: '{payload.topic}'")
    try:
        # Check if research is required
        if not ResearchService.research_required(payload.topic):
            logger.info("Topic evaluated as not requiring active search. Resolving with default info.")
            
        result = ResearchService.perform_research(
            db=db,
            topic=payload.topic,
            save_memory=payload.save_memory
        )
        return result
    except Exception as e:
        logger.error(f"Error executing API research query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Research processing failed: {str(e)}")
