from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from backend.app.core.database import get_db
from backend.app.services.executive.service import ExecutiveService
from backend.app.services.executive.attention import AttentionAllocationEngine
from backend.app.services.executive.briefing import BriefingGenerator
from backend.app.services.executive.reflection import ReflectionService
from backend.app.services.executive.critic import AgentCriticService

router = APIRouter(prefix="/api/executive", tags=["Executive Mind"])

# Schemas
class OpportunityRequest(BaseModel):
    title: str = Field(..., description="Title of the career or project opportunity")
    description: str | None = Field(None, description="Detailed explanation of the opportunity")
    relevance_score: float = Field(..., ge=0.0, le=5.0, description="Relevance importance rating from 0.0 to 5.0")
    source_url: str | None = Field(None, description="Web source reference link")

class RiskRequest(BaseModel):
    title: str = Field(..., description="Title of the threat or bottleneck risk")
    description: str | None = Field(None, description="Detailed context of the risk")
    severity: str = Field("medium", description="Risk level (low, medium, high, critical)")
    probability: float = Field(0.5, ge=0.0, le=1.0, description="Estimate probability from 0.0 to 1.0")
    mitigation_plan: str | None = Field(None, description="Plan to resolve or mitigate the risk")

# Endpoints
@router.get("/priorities")
def get_priorities(limit: int = 3, db: Session = Depends(get_db)):
    """
    Get top strategic task priorities (MITs) ranked by deadline proximity and weight.
    """
    try:
        tasks = ExecutiveService.get_most_important_tasks(db=db, limit=limit)
        return {"priorities": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch priorities: {str(e)}")

@router.get("/goals-alerts")
def get_goals_alerts(db: Session = Depends(get_db)):
    """
    Get list of goals currently behind schedule or missing subtask deadlines.
    """
    try:
        alerts = ExecutiveService.get_goals_behind_schedule(db=db)
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check goal health: {str(e)}")

@router.post("/opportunities")
def add_opportunity(request: OpportunityRequest, db: Session = Depends(get_db)):
    """
    Register a newly identified opportunity.
    """
    try:
        opp = ExecutiveService.add_opportunity(
            db=db,
            title=request.title,
            description=request.description,
            relevance_score=request.relevance_score,
            source_url=request.source_url
        )
        return {"status": "success", "opportunity_id": str(opp.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save opportunity: {str(e)}")

@router.get("/opportunities")
def list_opportunities(db: Session = Depends(get_db)):
    """
    List all active strategic opportunities.
    """
    try:
        opps = ExecutiveService.get_active_opportunities(db=db)
        return [
            {
                "id": str(o.id),
                "title": o.title,
                "description": o.description,
                "relevance_score": float(o.relevance_score),
                "source_url": o.source_url,
                "created_at": o.created_at.isoformat()
            } for o in opps
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve opportunities: {str(e)}")

@router.post("/risks")
def add_risk(request: RiskRequest, db: Session = Depends(get_db)):
    """
    Register a new strategic risk.
    """
    try:
        risk = ExecutiveService.add_risk(
            db=db,
            title=request.title,
            description=request.description,
            severity=request.severity,
            probability=request.probability,
            mitigation_plan=request.mitigation_plan
        )
        return {"status": "success", "risk_id": str(risk.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register risk: {str(e)}")

@router.get("/risks")
def list_risks(db: Session = Depends(get_db)):
    """
    List all active risks.
    """
    try:
        risks = ExecutiveService.get_active_risks(db=db)
        return [
            {
                "id": str(r.id),
                "title": r.title,
                "description": r.description,
                "severity": r.severity,
                "probability": float(r.probability),
                "mitigation_plan": r.mitigation_plan,
                "created_at": r.created_at.isoformat()
            } for r in risks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve risks: {str(e)}")

@router.get("/briefing/daily")
def get_daily_briefing(db: Session = Depends(get_db)):
    """
    Compile and generate the Daily Strategic Briefing in markdown.
    """
    try:
        briefing = BriefingGenerator.generate_daily_briefing(db=db)
        return {"briefing": briefing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily brief: {str(e)}")

@router.get("/briefing/weekly")
def get_weekly_review(db: Session = Depends(get_db)):
    """
    Compile and generate the Weekly Retrospective Review in markdown.
    """
    try:
        review = BriefingGenerator.generate_weekly_review(db=db)
        return {"review": review}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate weekly review: {str(e)}")

@router.get("/attention/summary")
def get_attention_summary(timeframe_hours: int = 24, db: Session = Depends(get_db)):
    """
    Get aggregated activity summaries, efficiency scores, and budget alignment status.
    """
    try:
        summary = AttentionAllocationEngine.get_attention_summary(db=db, timeframe_hours=timeframe_hours)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve attention summary: {str(e)}")

@router.post("/reflect")
def trigger_reflection(db: Session = Depends(get_db)):
    """
    Trigger a manual daily reflection calculation.
    """
    try:
        res = ReflectionService.generate_reflection(db=db)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute daily reflection: {str(e)}")

@router.get("/reflections")
def list_reflections(limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve the history of daily reflection logs.
    """
    try:
        history = ReflectionService.get_reflection_history(db=db, limit=limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reflections history: {str(e)}")

@router.post("/evaluate")
def trigger_evaluation(db: Session = Depends(get_db)):
    """
    Trigger an immediate agent performance evaluation.
    """
    try:
        res = AgentCriticService.evaluate_agent_performance(db=db)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute agent evaluation: {str(e)}")

@router.get("/evaluations")
def list_evaluations(limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve historical agent evaluations.
    """
    try:
        history = AgentCriticService.get_evaluation_history(db=db, limit=limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evaluations history: {str(e)}")
