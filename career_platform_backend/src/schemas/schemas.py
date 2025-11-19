from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class ProgressStatus(str, Enum):
    """Enumeration representing progress state for a user's competency."""
    not_started = "not_started"
    working_on = "working_on"
    completed = "completed"


class RoleOut(BaseModel):
    """Serializable role representation."""
    id: int = Field(..., description="Role ID")
    name: str = Field(..., description="Name of the role")
    description: Optional[str] = Field(None, description="Optional description for the role")

    class Config:
        from_attributes = True


class CompetencyOut(BaseModel):
    """Serializable competency representation."""
    id: int = Field(..., description="Competency ID")
    name: str = Field(..., description="Name of the competency")
    category: str = Field(..., description="Category such as Technical, Leadership, etc.")
    description: Optional[str] = Field(None, description="Optional description")

    class Config:
        from_attributes = True


class RoleCompetencyOut(BaseModel):
    """Mapping from role to competency with required level."""
    competency: CompetencyOut
    required_level: int = Field(..., description="Required level for the role on a 1-5 scale")

    class Config:
        from_attributes = True


class CompetencyModelOut(BaseModel):
    """A role's competency model - the set of competencies and required levels."""
    role: RoleOut
    requirements: List[RoleCompetencyOut]


class UserCompetencyOut(BaseModel):
    """User or session's current competency progression state."""
    id: int
    session_id: Optional[str]
    user_id: Optional[int]
    competency: CompetencyOut
    current_level: int
    status: ProgressStatus

    class Config:
        from_attributes = True


class RoadmapOut(BaseModel):
    """Serialized roadmap, payload is JSON string for MVP."""
    id: int
    session_id: Optional[str]
    role_from: int
    role_to: int
    created_at: datetime
    payload: str = Field(..., description="JSON string of roadmap structure")

    class Config:
        from_attributes = True
