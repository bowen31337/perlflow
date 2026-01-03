"""SMS notification schemas."""

from datetime import datetime
from typing import Optional, Union

import pydantic
from pydantic import BaseModel, Field

from src.models.sms_notification import SMSNotificationStatus, SMSNotificationType


class SMSNotificationBase(BaseModel):
    """Base schema for SMS notifications."""

    appointment_id: Optional[str] = None
    patient_id: str
    clinic_id: str
    message_type: SMSNotificationType
    phone_number: str = Field(..., description="E.164 formatted phone number")
    message_content: str
    scheduled_time: datetime


class SMSNotificationCreate(SMSNotificationBase):
    """Schema for creating SMS notifications."""

    pass


class SMSNotificationResponse(SMSNotificationBase):
    """Schema for SMS notification responses."""

    id: str
    sent_time: Optional[datetime] = None
    status: SMSNotificationStatus
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class SMSReminderRequest(BaseModel):
    """Request schema for creating appointment reminders."""

    appointment_id: str = Field(..., description="ID of the appointment to remind")
    reminder_hours: int = Field(
        default=24, description="Hours before appointment to send reminder"
    )


class SMSReminderResponse(BaseModel):
    """Response schema for SMS reminder creation."""

    message: str
    notification_id: str


class SMSStatusResponse(BaseModel):
    """Response schema for SMS status."""

    notification_id: str
    status: SMSNotificationStatus
    sent_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int