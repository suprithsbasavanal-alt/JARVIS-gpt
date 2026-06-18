from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from backend.app.core.database import get_db
from backend.app.services.identity.service import IdentityService

router = APIRouter(prefix="/api/identity", tags=["Identity Engine"])

# Schemas
class ExtractRequest(BaseModel):
    text: str = Field(..., description="Conversational text input to scan for identity elements")

class ExtractResponse(BaseModel):
    status: str
    extracted: list[dict]

class ReinforceRequest(BaseModel):
    key: str = Field(..., description="Identity key to reinforce or create")
    value: str = Field(..., description="Content value of the identity element")
    category: str = Field(..., description="Classification category (e.g. value, preference, motivation)")
    score_increment: float = Field(0.5, ge=0.0, le=2.0, description="Amount to increment salience by")

class ReinforceResponse(BaseModel):
    status: str
    key: str
    new_score: float

# Endpoints
@router.post("/extract", response_model=ExtractResponse)
def extract_identity(request: ExtractRequest, db: Session = Depends(get_db)):
    """
    Scan conversation input, detect values/preferences, and automatically update identity models.
    """
    try:
        results = IdentityService.extract_and_integrate_from_text(db=db, text=request.text)
        return ExtractResponse(status="success", extracted=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identity extraction failed: {str(e)}")

@router.get("/profile")
def get_identity_profile(db: Session = Depends(get_db)):
    """
    Compile and return the complete consolidated user identity profile.
    """
    try:
        profile = IdentityService.get_identity_profile(db=db)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {str(e)}")

@router.post("/reinforce", response_model=ReinforceResponse)
def reinforce_identity(request: ReinforceRequest, db: Session = Depends(get_db)):
    """
    Manually inject or reinforce a value, preference, or motivation in the identity model.
    """
    try:
        db_item = IdentityService.reinforce_or_store_identity_item(
            db=db,
            key=request.key,
            value=request.value,
            category=request.category,
            score_increment=request.score_increment
        )
        return ReinforceResponse(
            status="success",
            key=db_item.entity_key,
            new_score=float(db_item.salience_score)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reinforce identity item: {str(e)}")
