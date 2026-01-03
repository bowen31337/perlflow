"""SMS notification database model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SMSNotificationStatus(str, enum.Enum):
    """SMS notification status enumeration."""

    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"
    EXPIRED = "EXPIRED"


class SMSNotificationType(str, enum.Enum):
    """SMS notification type enumeration."""

    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"
    APPOINTMENT_CONFIRMATION = "APPOINTMENT_CONFIRMATION"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    MOVE_OFFER = "MOVE_OFFER"
    WAITLIST_AVAILABLE = "WAITLIST_AVAILABLE"


class SMSNotification(Base):
    """SMS notification model for appointment reminders and updates."""

    __tablename__ = "sms_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Appointment ID if notification is related to an appointment",
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
    message_type: Mapped[SMSNotificationType] = mapped_column(
        Enum(SMSNotificationType),
        nullable=False,
    )
    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="E.164 formatted phone number",
    )
    message_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the SMS should be sent",
    )
    sent_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the SMS was actually sent",
    )
    status: Mapped[SMSNotificationStatus] = mapped_column(
        Enum(SMSNotificationStatus),
        default=SMSNotificationStatus.PENDING,
        index=True,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="SMS provider message ID for tracking",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if notification failed",
    )
    retry_count: Mapped[int] = mapped_column(
        default=0,
        comment="Number of retry attempts",
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
        return f"<SMSNotification(id={self.id}, patient_id={self.patient_id}, type={self.message_type}, status={self.status})>"