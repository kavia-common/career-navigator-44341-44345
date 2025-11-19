from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import User, UserCompetency, Competency, ProgressStatusEnum


def _ensure_user(db: Session, user_id: Optional[int]) -> Optional[User]:
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id)  # allow deterministic fixtures for MVP
        db.add(user)
        db.flush()
    return user


# PUBLIC_INTERFACE
def upsert_user_competency(
    db: Session,
    *,
    competency_id: int,
    current_level: int,
    status: ProgressStatusEnum,
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> UserCompetency:
    """Create or update competency assessment for a user or anonymous session."""
    if user_id:
        _ensure_user(db, user_id)

    # Try fetch existing record based on user or session
    crit = []
    if user_id:
        crit.append(UserCompetency.user_id == user_id)
    if session_id:
        crit.append(UserCompetency.session_id == session_id)

    stmt = (
        select(UserCompetency)
        .where(UserCompetency.competency_id == competency_id)
        .where((crit[0] if crit else (UserCompetency.session_id == session_id)))
    )
    if user_id and session_id:
        stmt = stmt.where(
            (UserCompetency.user_id == user_id) | (UserCompetency.session_id == session_id)
        )

    instance = db.scalars(stmt.limit(1)).first()

    if instance is None:
        instance = UserCompetency(
            competency_id=competency_id,
            current_level=current_level,
            status=status,
            session_id=session_id,
            user_id=user_id,
        )
        db.add(instance)
    else:
        instance.current_level = current_level
        instance.status = status

    db.flush()
    return instance


# PUBLIC_INTERFACE
def get_assessment_snapshot(
    db: Session, *, session_id: Optional[str] = None, user_id: Optional[int] = None
) -> List[UserCompetency]:
    """Return all competencies with current levels for a user or session."""
    stmt = select(UserCompetency).join(Competency, Competency.id == UserCompetency.competency_id)
    if user_id is not None:
        stmt = stmt.where(UserCompetency.user_id == user_id)
    elif session_id is not None:
        stmt = stmt.where(UserCompetency.session_id == session_id)
    else:
        return []
    return list(db.scalars(stmt).all())
