from typing import List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from src.core.db import Base, engine, SessionLocal
from src.models import Role, Competency, RoleCompetency
from src.api.routers.roles import router as roles_router
from src.api.routers.assessments import router as assessments_router
from src.api.routers.roadmaps import router as roadmaps_router

openapi_tags = [
    {"name": "Roles", "description": "Role directory and competency models"},
    {"name": "Assessments", "description": "User/session competency assessments and progress"},
    {"name": "Roadmaps", "description": "Gap analysis and roadmap generation/retrieval"},
]

# Create FastAPI app with extended metadata
app = FastAPI(
    title="Career Navigator Backend",
    description=(
        "Backend API for role competency modeling, assessments, and career roadmaps.\n\n"
        "Usage notes:\n"
        "- Start by fetching roles and their competency models.\n"
        "- Record assessments for the current user or anonymous session.\n"
        "- Generate a roadmap from role A to role B; payload includes mind map JSON.\n"
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_init() -> None:
    """
    Create all tables and seed initial data on first run.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed data if roles table is empty
    db: Session = SessionLocal()
    try:
        roles_count = db.query(Role).count()
        if roles_count == 0:
            seed_initial_data(db)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def seed_initial_data(db: Session) -> None:
    """
    Populate initial roles, competencies, and role-competency mappings.
    Ensures >=3 roles, >=8 competencies across categories, and mappings with required_level 1-5.
    """
    # Roles
    roles = [
        Role(name="Software Engineer", description="Builds and maintains software systems."),
        Role(name="Engineering Manager", description="Leads engineering teams and delivery."),
        Role(name="Chief Architect", description="Sets technical vision and architecture."),
    ]
    db.add_all(roles)
    db.flush()  # obtain IDs

    # Competencies across categories
    competencies = [
        Competency(name="System Design", category="Technical", description="Design scalable systems."),
        Competency(name="Coding Excellence", category="Technical", description="High-quality code practices."),
        Competency(name="DevOps & Reliability", category="Technical", description="CI/CD, observability."),
        Competency(name="People Leadership", category="Leadership", description="Coaching and team growth."),
        Competency(name="Stakeholder Management", category="Business", description="Manage expectations."),
        Competency(name="Product Thinking", category="Business", description="Outcome-oriented delivery."),
        Competency(name="Strategic Vision", category="Strategy", description="Long-term technology vision."),
        Competency(name="Communication", category="Leadership", description="Clear written and verbal comms."),
        Competency(name="Execution & Delivery", category="Execution", description="Plan and deliver reliably."),
    ]
    db.add_all(competencies)
    db.flush()

    # Helper to get by name for mapping
    def get_role(name: str) -> Role:
        return next(r for r in roles if r.name == name)

    def get_comp(name: str) -> Competency:
        return next(c for c in competencies if c.name == name)

    # Role-Competency mappings (required_level 1-5)
    mappings: List[Tuple[str, str, int]] = [
        # Software Engineer emphasis
        ("Software Engineer", "Coding Excellence", 4),
        ("Software Engineer", "System Design", 3),
        ("Software Engineer", "DevOps & Reliability", 3),
        ("Software Engineer", "Communication", 3),
        ("Software Engineer", "Execution & Delivery", 3),

        # Engineering Manager emphasis
        ("Engineering Manager", "People Leadership", 4),
        ("Engineering Manager", "Stakeholder Management", 4),
        ("Engineering Manager", "Communication", 4),
        ("Engineering Manager", "Execution & Delivery", 4),
        ("Engineering Manager", "Product Thinking", 3),

        # Chief Architect emphasis
        ("Chief Architect", "Strategic Vision", 5),
        ("Chief Architect", "System Design", 5),
        ("Chief Architect", "Communication", 4),
        ("Chief Architect", "DevOps & Reliability", 4),
        ("Chief Architect", "Product Thinking", 4),
    ]

    rc_entities = [
        RoleCompetency(
            role_id=get_role(rn).id,
            competency_id=get_comp(cn).id,
            required_level=level,
        )
        for rn, cn, level in mappings
    ]
    db.add_all(rc_entities)


@app.get("/", summary="Health Check", tags=["Roles"])
def health_check():
    """
    Health Check
    Simple endpoint to verify the service is running.
    Returns {"message": "Healthy"} when operational.
    """
    return {"message": "Healthy"}


# Register routers
app.include_router(roles_router)
app.include_router(assessments_router)
app.include_router(roadmaps_router)
