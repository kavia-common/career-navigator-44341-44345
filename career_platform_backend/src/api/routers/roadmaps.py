from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.schemas import RoadmapOut
from src.services import roadmaps as svc

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


class GenerateRoadmapIn(BaseModel):
    role_from_id: int = Field(..., description="Current role id")
    role_to_id: int = Field(..., description="Target role id")
    session_id: Optional[str] = Field(None, description="Anonymous session id")
    user_id: Optional[int] = Field(None, description="User id if authenticated")


@router.post(
    "/generate",
    summary="Generate roadmap",
    description="Perform gap analysis and generate a mind map JSON with deterministic recommendations.",
    response_model=RoadmapOut,
)
# PUBLIC_INTERFACE
def generate(payload: GenerateRoadmapIn, db: Session = Depends(get_db)):
    """Generate and persist a roadmap for the provided user/session and roles."""
    try:
        rm = svc.generate_roadmap(
            db,
            role_from_id=payload.role_from_id,
            role_to_id=payload.role_to_id,
            session_id=payload.session_id,
            user_id=payload.user_id,
        )
        db.commit()
        return RoadmapOut.model_validate(rm)
    except ValueError as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ex))


@router.get(
    "/",
    summary="List roadmaps",
    description="List roadmaps belonging to the provided session or user.",
    response_model=List[RoadmapOut],
)
# PUBLIC_INTERFACE
def list_for_owner(session_id: Optional[str] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List available roadmaps for the provided principal."""
    rows = svc.list_roadmaps(db, session_id=session_id, user_id=user_id)
    return [RoadmapOut.model_validate(r) for r in rows]


@router.get(
    "/{roadmap_id}",
    summary="Get roadmap by id",
    description="Retrieve a single roadmap record with payload JSON string.",
    response_model=RoadmapOut,
)
# PUBLIC_INTERFACE
def get_by_id(roadmap_id: int, db: Session = Depends(get_db)):
    """Fetch specific roadmap by id."""
    rm = svc.get_roadmap(db, roadmap_id)
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return RoadmapOut.model_validate(rm)
