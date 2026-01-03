"""Appointment database model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.clinic import Clinic
    from src.models.dentist import Dentist
    from src.models.patient import Patient


class AppointmentStatus(str, enum.Enum):
    """Appointment status enumeration."""

    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    OFFERING_MOVE = "OFFERING_MOVE"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class Appointment(Base):
    """Appointment model for dental appointments."""

    __tablename__ = "appointments"

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
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dentist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dentists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Appointment start time in UTC",
    )
    duration_mins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )
    procedure_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Dental procedure code (e.g., D1110)",
    )
    procedure_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estimated_value: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Estimated revenue value for heuristics",
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.BOOKED,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="appointments",
        lazy="selectin",
    )
    clinic: Mapped["Clinic"] = relationship(
        "Clinic",
        back_populates="appointments",
        lazy="selectin",
    )
    dentist: Mapped["Dentist"] = relationship(
        "Dentist",
        back_populates="appointments",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, start_time={self.start_time})>"
