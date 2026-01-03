"""
Wrapper module for backward compatibility.
The actual models are in the models/ directory.
"""
from src.models import (
    Patient, Appointment, AppointmentStatus, Clinic, Dentist, Procedure,
    AgentSession, SessionStatus, MoveOffer, MoveOfferStatus, IncentiveType,
    Feedback, SMSNotification, SMSNotificationStatus, SMSNotificationType,
    Waitlist, WaitlistNotification
)

# Re-export for backward compatibility
__all__ = [
    "Patient",
    "Appointment",
    "AppointmentStatus",
    "Clinic",
    "Dentist",
    "Procedure",
    "AgentSession",
    "SessionStatus",
    "MoveOffer",
    "MoveOfferStatus",
    "IncentiveType",
    "Feedback",
    "SMSNotification",
    "SMSNotificationStatus",
    "SMSNotificationType",
    "Waitlist",
    "WaitlistNotification",
]

# Also export Base for extensibility tests
from src.core.database import Base
__all__.append("Base")
