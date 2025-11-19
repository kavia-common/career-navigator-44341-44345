from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.schemas import UserCompetencyOut, ProgressStatus
from src.models import ProgressStatusEnum
from src.services import assessments as svc

router = APIRouter(prefix="/assessments", tags=["Assessments"])


class AssessmentIn(BaseModel):
    competency_id: int = Field(..., description="Competency identifier")
    current_level: int = Field(..., ge=0, le=5, description="Current level on 0-5 scale")
    status: ProgressStatus = Field(..., description="Progress status")
    session_id: Optional[str] = Field(None, description="Anonymous session id")
    user_id: Optional[int] = Field(None, description="User id if authenticated")


@router.post(
    "/",
    summary="Create or update assessment",
    description="Upsert a user's or session's competency assessment row.",
    response_model=UserCompetencyOut,
)
# PUBLIC_INTERFACE
def upsert_assessment(payload: AssessmentIn, db: Session = Depends(get_db)):
    """Create or update an assessment entry for a competency."""
    inst = svc.upsert_user_competency(
        db,
        competency_id=payload.competency_id,
        current_level=payload.current_level,
        status=ProgressStatusEnum(payload.status.value),
        session_id=payload.session_id,
        user_id=payload.user_id,
    )
    return UserCompetencyOut.model_validate(inst)


@router.get(
    "/snapshot",
    summary="Get assessment snapshot",
    description="Return all competency assessment rows for a user or session.",
    response_model=List[UserCompetencyOut],
)
# PUBLIC_INTERFACE
def get_snapshot(session_id: Optional[str] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Fetch snapshot of assessments."""
    rows = svc.get_assessment_snapshot(db, session_id=session_id, user_id=user_id)
    return [UserCompetencyOut.model_validate(r) for r in rows]
