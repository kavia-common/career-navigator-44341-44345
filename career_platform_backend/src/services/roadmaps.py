import json
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    Role,
    RoleCompetency,
    Competency,
    UserCompetency,
    Roadmap,
)


def _collect_role_requirements(db: Session, role_id: int) -> List[Tuple[Competency, int]]:
    stmt = (
        select(Competency, RoleCompetency.required_level)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .where(RoleCompetency.role_id == role_id)
    )
    # Convert rows to a tuple list explicitly
    results = db.execute(stmt).all()
    # Convert SQLAlchemy result rows to list of (Competency, required_level)
    return [(c, req) for c, req in results]


def _current_level_for(
    db: Session, comp_id: int, *, session_id: Optional[str], user_id: Optional[int]
) -> int:
    stmt = select(UserCompetency).where(UserCompetency.competency_id == comp_id)
    if user_id is not None:
        stmt = stmt.where(UserCompetency.user_id == user_id)
    elif session_id is not None:
        stmt = stmt.where(UserCompetency.session_id == session_id)
    else:
        return 0
    inst = db.scalars(stmt.limit(1)).first()
    return inst.current_level if inst else 0


def _deterministic_recommendations(category: str, name: str, gap: int) -> List[str]:
    base = [
        f"Study fundamentals of {name}",
        f"Build a small project highlighting {name}",
        f"Document learnings and outcomes",
    ]
    if category.lower() in {"leadership", "people"}:
        base.append("Shadow a senior leader for decision-making patterns")
        base.append("Lead a small initiative with clear success metrics")
    if category.lower() in {"technical", "strategy"}:
        base.append("Read a well-regarded book in this area and summarize takeaways")
        base.append("Create a design doc and get feedback")
    if gap >= 3:
        base.append("Enroll in an advanced course and apply concepts at work")
    return base[:5]


def _mind_map_from_gaps(
    role_from: Role,
    role_to: Role,
    gaps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    # Cytoscape/D3-friendly simple structure
    nodes = [
        {"id": "you", "label": "You Today"},
        {"id": f"role:{role_to.id}", "label": f"Target: {role_to.name}"},
    ]
    edges = [{"source": "you", "target": f"role:{role_to.id}", "label": "Goal"}]

    # Group by category
    categories = {}
    for g in gaps:
        cat = g["competency"]["category"]
        categories.setdefault(cat, [])
        categories[cat].append(g)

    for cat, items in categories.items():
        cat_id = f"cat:{cat}"
        nodes.append({"id": cat_id, "label": cat})
        edges.append({"source": f"role:{role_to.id}", "target": cat_id, "label": "Area"})
        for g in items:
            comp_id = f"comp:{g['competency']['id']}"
            label = f"{g['competency']['name']} (req {g['required_level']}, cur {g['current_level']})"
            nodes.append({"id": comp_id, "label": label, "gap": g["gap"]})
            gap_label = "gap " + str(g["gap"])
            edges.append({"source": cat_id, "target": comp_id, "label": gap_label})

    return {"nodes": nodes, "edges": edges}


# PUBLIC_INTERFACE
def generate_roadmap(
    db: Session,
    *,
    role_from_id: int,
    role_to_id: int,
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Roadmap:
    """Create a roadmap performing gap analysis and storing a JSON payload with mind-map and recommendations."""
    rf = db.get(Role, role_from_id)
    rt = db.get(Role, role_to_id)
    if rf is None or rt is None:
        raise ValueError("Invalid roles provided")

    requirements = _collect_role_requirements(db, role_to_id)

    gaps: List[Dict[str, Any]] = []
    for comp, required in requirements:
        current = _current_level_for(db, comp.id, session_id=session_id, user_id=user_id)
        gap = max(0, required - current)
        gaps.append(
            {
                "competency": {
                    "id": comp.id,
                    "name": comp.name,
                    "category": comp.category,
                    "description": comp.description,
                },
                "required_level": required,
                "current_level": current,
                "gap": gap,
                "recommendations": _deterministic_recommendations(comp.category, comp.name, gap),
            }
        )

    # Build payload
    mind_map = _mind_map_from_gaps(rf, rt, gaps)
    payload_dict = {
        "meta": {
            "from_role": {"id": rf.id, "name": rf.name},
            "to_role": {"id": rt.id, "name": rt.name},
        },
        "gaps": gaps,
        "mind_map": mind_map,
    }
    payload = json.dumps(payload_dict)

    roadmap = Roadmap(
        session_id=session_id,
        role_from=role_from_id,
        role_to=role_to_id,
        payload=payload,
    )
    db.add(roadmap)
    db.flush()
    return roadmap


# PUBLIC_INTERFACE
def list_roadmaps(
    db: Session, *, session_id: Optional[str] = None, user_id: Optional[int] = None
) -> List[Roadmap]:
    """List roadmaps belonging to the user or session."""
    stmt = select(Roadmap).order_by(Roadmap.created_at.desc())
    # MVP: associate roadmaps to sessions only; user_id not persisted yet.
    if session_id:
        stmt = stmt.where(Roadmap.session_id == session_id)
    return list(db.scalars(stmt).all())


# PUBLIC_INTERFACE
def get_roadmap(db: Session, roadmap_id: int) -> Optional[Roadmap]:
    """Fetch a specific roadmap by id."""
    return db.get(Roadmap, roadmap_id)
