"""Feedback database model for patient reviews (AHPRA compliance required)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.patient import Patient


class Feedback(Base):
    """Feedback model for patient reviews with AHPRA compliance tracking."""

    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Rating from 1-5",
    )
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Feedback text content",
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="AHPRA compliance: requires manual approval",
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Admin user who approved",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="feedback",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, rating={self.rating}, approved={self.is_approved})>"
