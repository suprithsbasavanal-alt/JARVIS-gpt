import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, AuditLog
from backend.app.services.automation.service import AutomationService
from backend.app.services.automation.safety import AuditSystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["Automation Enclave"])

class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict

class ExecuteResponse(BaseModel):
    status: str
    output: str | None = None
    audit_id: str | None = None
    reason: str | None = None

class AuditLogItem(BaseModel):
    id: str
    action_type: str
    command_payload: str
    is_approved: bool
    created_at: str
    approved_at: str | None = None

@router.post("/execute", response_model=ExecuteResponse)
def execute_tool(payload: ExecuteRequest, db: Session = Depends(get_db)):
    """
    Executes an automation tool. High-risk actions will be blocked and returns 'pending_approval'.
    """
    logger.info(f"API execute_tool invoked for tool: '{payload.tool_name}'")
    try:
        res = AutomationService.execute_action(
            db=db,
            tool_name=payload.tool_name,
            arguments=payload.arguments
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error executing API automation tool: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Automation tool failed: {str(e)}")

@router.post("/approve/{audit_id}", response_model=ExecuteResponse)
def approve_and_run(audit_id: str, db: Session = Depends(get_db)):
    """
    Approves a previously blocked high-risk action and executes it.
    """
    logger.info(f"API approve_and_run invoked for audit_id: '{audit_id}'")
    try:
        uuid_id = uuid.UUID(audit_id)
        res = AutomationService.execute_pending_action(db, uuid_id)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error approving and executing action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Approval execution failed: {str(e)}")

@router.get("/audit", response_model=list[AuditLogItem])
def get_audit_history(db: Session = Depends(get_db)):
    """
    Retrieves complete action audit log history.
    """
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    return [
        AuditLogItem(
            id=str(log.id),
            action_type=log.action_type,
            command_payload=log.command_payload,
            is_approved=log.is_approved,
            created_at=log.created_at.isoformat(),
            approved_at=log.approved_at.isoformat() if log.approved_at else None
        ) for log in logs
    ]
