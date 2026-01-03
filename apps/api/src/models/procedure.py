"""Procedure database model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Procedure(Base):
    """Procedure model for dental procedures."""

    __tablename__ = "procedures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Procedure code (e.g., D1110 for Prophylaxis)",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Procedure category (e.g., Preventive, Restorative)",
    )
    default_duration_mins: Mapped[int] = mapped_column(
        Integer,
        default=30,
    )
    base_value: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Base revenue value",
    )
    priority_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        comment="Priority weight for scheduling heuristics",
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

    def __repr__(self) -> str:
        return f"<Procedure(code='{self.code}', name='{self.name}')>"
