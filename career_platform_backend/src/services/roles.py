from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Role, Competency, RoleCompetency


# PUBLIC_INTERFACE
def list_roles(db: Session) -> List[Role]:
    """Return all available roles."""
    return list(db.scalars(select(Role).order_by(Role.name)).all())


# PUBLIC_INTERFACE
def get_role_competency_model(db: Session, role_id: int) -> Dict[str, Any]:
    """Return the competency model for a given role including required levels by category."""
    role: Role | None = db.get(Role, role_id)
    if not role:
        raise ValueError("Role not found")

    stmt = (
        select(RoleCompetency, Competency)
        .join(Competency, RoleCompetency.competency_id == Competency.id)
        .where(RoleCompetency.role_id == role_id)
        .order_by(Competency.category, Competency.name)
    )
    rows = db.execute(stmt).all()

    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for rc, comp in rows:
        by_category.setdefault(comp.category, []).append(
            {
                "competency": {
                    "id": comp.id,
                    "name": comp.name,
                    "category": comp.category,
                    "description": comp.description,
                },
                "required_level": rc.required_level,
            }
        )

    return {
        "role": {"id": role.id, "name": role.name, "description": role.description},
        "requirements": by_category,
    }
