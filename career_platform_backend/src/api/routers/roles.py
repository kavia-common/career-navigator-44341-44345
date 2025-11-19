from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.schemas import RoleOut, RoleCompetencyOut
from src.services import roles as roles_service

router = APIRouter(prefix="/roles", tags=["Roles"], responses={404: {"description": "Not found"}})


@router.get(
    "/",
    summary="List roles",
    description="Retrieve the list of available roles.",
    response_model=List[RoleOut],
)
# PUBLIC_INTERFACE
def list_roles(db: Session = Depends(get_db)):
    """Return all available roles."""
    return roles_service.list_roles(db)


class CompetencyModelByCategory(BaseModel):
    role: RoleOut = Field(..., description="Role info")
    requirements: Dict[str, List[RoleCompetencyOut]] = Field(
        ..., description="Mapping of category name to list of competency requirements"
    )


@router.get(
    "/{role_id}/competency-model",
    summary="Get competency model",
    description="Retrieve the competency model for a role, grouped by category.",
    response_model=CompetencyModelByCategory,
)
# PUBLIC_INTERFACE
def get_competency_model(role_id: int, db: Session = Depends(get_db)):
    """Return competency requirements for a role."""
    try:
        data: Dict[str, Any] = roles_service.get_role_competency_model(db, role_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Role not found")
    # Convert service dict to schema
    role = RoleOut(**data["role"])
    mapped: Dict[str, List[RoleCompetencyOut]] = {}
    for cat, items in data["requirements"].items():
        mapped[cat] = [RoleCompetencyOut(**i) for i in items]
    return CompetencyModelByCategory(role=role, requirements=mapped)
