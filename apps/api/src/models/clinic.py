"""Clinic database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.appointment import Appointment
    from src.models.dentist import Dentist
    from src.models.session import AgentSession


class Clinic(Base):
    """Clinic model for dental practice information."""

    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Australia/Sydney",
        comment="IANA timezone string",
    )
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        comment="Clinic settings: operating_hours, slot_duration, etc.",
    )
    api_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="API key for widget authentication",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    dentists: Mapped[list["Dentist"]] = relationship(
        "Dentist",
        back_populates="clinic",
        lazy="selectin",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="clinic",
        lazy="selectin",
    )
    sessions: Mapped[list["AgentSession"]] = relationship(
        "AgentSession",
        back_populates="clinic",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Clinic(id={self.id}, name='{self.name}')>"
