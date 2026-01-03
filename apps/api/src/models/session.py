"""Agent Session database model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.clinic import Clinic
    from src.models.patient import Patient


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class AgentSession(Base):
    """Agent session model for tracking conversation state."""

    __tablename__ = "agent_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Session ID used as thread_id for LangGraph",
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Nullable for anonymous sessions",
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        comment="LangGraph checkpoint state",
    )
    current_node: Mapped[str] = mapped_column(
        String(100),
        default="Receptionist",
        comment="Active agent: Receptionist, IntakeSpecialist, ResourceOptimiser",
    )
    messages: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        comment="Conversation history",
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        default=SessionStatus.ACTIVE,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship(
        "Clinic",
        back_populates="sessions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AgentSession(session_id={self.session_id}, status={self.status})>"
