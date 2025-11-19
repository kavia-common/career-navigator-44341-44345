from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    DateTime,
    Text,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


class ProgressStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    WORKING_ON = "working_on"
    COMPLETED = "completed"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role_competencies: Mapped[list["RoleCompetency"]] = relationship(
        "RoleCompetency", back_populates="role", cascade="all, delete-orphan"
    )


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)  # Technical, Leadership, etc.
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role_competencies: Mapped[list["RoleCompetency"]] = relationship(
        "RoleCompetency", back_populates="competency", cascade="all, delete-orphan"
    )
    user_competencies: Mapped[list["UserCompetency"]] = relationship(
        "UserCompetency", back_populates="competency", cascade="all, delete-orphan"
    )


class RoleCompetency(Base):
    __tablename__ = "role_competencies"
    __table_args__ = (UniqueConstraint("role_id", "competency_id", name="uq_role_competency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False, index=True)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 scale

    role: Mapped["Role"] = relationship("Role", back_populates="role_competencies")
    competency: Mapped["Competency"] = relationship("Competency", back_populates="role_competencies")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), unique=True, nullable=True, index=True)

    competencies: Mapped[list["UserCompetency"]] = relationship(
        "UserCompetency", back_populates="user", cascade="all, delete-orphan"
    )


class UserCompetency(Base):
    __tablename__ = "user_competencies"
    __table_args__ = (
        # user_id or session_id combined with competency should be unique to avoid duplicates
        UniqueConstraint("user_id", "competency_id", name="uq_user_competency_user"),
        UniqueConstraint("session_id", "competency_id", name="uq_user_competency_session"),
        Index("ix_user_or_session", "user_id", "session_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False, index=True)
    current_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ProgressStatusEnum] = mapped_column(
        SAEnum(ProgressStatusEnum, name="progress_status_enum"),
        default=ProgressStatusEnum.NOT_STARTED,
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="competencies")
    competency: Mapped["Competency"] = relationship("Competency", back_populates="user_competencies")


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    role_from: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    role_to: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # Stored JSON string

    # Note: relationships omitted for simplicity
