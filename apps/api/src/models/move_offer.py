"""Move Offer database model for appointment rescheduling incentives."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class IncentiveType(str, enum.Enum):
    """Incentive type enumeration."""

    DISCOUNT = "DISCOUNT"
    PRIORITY_SLOT = "PRIORITY_SLOT"
    GIFT = "GIFT"


class MoveOfferStatus(str, enum.Enum):
    """Move offer status enumeration."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class MoveOffer(Base):
    """Move offer model for appointment rescheduling incentives."""

    __tablename__ = "move_offers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    original_appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        comment="New appointment if offer accepted",
    )
    incentive_type: Mapped[IncentiveType] = mapped_column(
        Enum(IncentiveType),
        nullable=False,
    )
    incentive_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Discount percentage or value of gift",
    )
    move_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Calculated move score (0-100)",
    )
    status: Mapped[MoveOfferStatus] = mapped_column(
        Enum(MoveOfferStatus),
        default=MoveOfferStatus.PENDING,
        index=True,
    )
    offered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<MoveOffer(id={self.id}, status={self.status}, score={self.move_score})>"
