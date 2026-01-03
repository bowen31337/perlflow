"""Dentist database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.appointment import Appointment
    from src.models.clinic import Clinic


class Dentist(Base):
    """Dentist model for dental practitioners."""

    __tablename__ = "dentists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specializations: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        comment="List of specializations (e.g., implants, orthodontics)",
    )
    schedule: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        comment="Weekly availability schedule",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    clinic: Mapped["Clinic"] = relationship(
        "Clinic",
        back_populates="dentists",
        lazy="selectin",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="dentist",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Dentist(id={self.id}, name='{self.name}')>"
