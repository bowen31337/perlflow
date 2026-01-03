"""Patient database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, String, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.appointment import Appointment
    from src.models.feedback import Feedback


class Patient(Base):
    """Patient model for storing patient information."""

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="E.164 format phone number",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_profile: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Risk profile with pain_tolerance, anxiety_level",
    )
    ltv_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Lifetime value score for heuristics",
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
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        lazy="selectin",
    )
    feedback: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="patient",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, name='{self.name}', phone='{self.phone}')>"
