"""
Waitlist model for PearlFlow
Handles patient waitlist entries when no appointments are available.
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from src.core.database import Base
import uuid


class Waitlist(Base):
    """Waitlist model for patients requesting appointments when none available."""

    __tablename__ = "waitlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    clinic_id = Column(String, ForeignKey("clinics.id"), nullable=False)

    # Patient preferences
    preferred_date_range = Column(JSON, nullable=True)  # {"start": "2024-01-15", "end": "2024-01-20"}
    preferred_time = Column(String, nullable=True)  # "morning", "afternoon", "evening"
    procedure_code = Column(String, nullable=True)  # e.g., "D1110"

    # Waitlist status
    status = Column(String, default="active")  # active, filled, cancelled
    priority_score = Column(Integer, default=0)  # Higher = more urgent

    # Notification tracking
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime, nullable=True)
    response = Column(String, nullable=True)  # accepted, declined, no_response

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Waitlist(id={self.id}, patient_id={self.patient_id}, status={self.status})>"


class WaitlistNotification(Base):
    """Track notifications sent to waitlist patients."""

    __tablename__ = "waitlist_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    waitlist_id = Column(String, ForeignKey("waitlist.id"), nullable=False)
    notification_type = Column(String, nullable=False)  # slot_available, reminder
    sent_at = Column(DateTime, default=func.now())
    response = Column(String, nullable=True)  # accepted, declined, no_response

    def __repr__(self):
        return f"<WaitlistNotification(id={self.id}, type={self.notification_type})>"
