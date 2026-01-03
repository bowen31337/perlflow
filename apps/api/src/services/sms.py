"""SMS notification service for appointment reminders and updates."""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.appointment import Appointment
from src.models.clinic import Clinic
from src.models.patient import Patient
from src.models.sms_notification import SMSNotification, SMSNotificationStatus, SMSNotificationType
from src.schemas.sms import SMSNotificationCreate, SMSNotificationResponse, SMSReminderRequest


class SMSNotificationService:
    """Service for handling SMS notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_appointment_reminder(
        self, appointment_id: uuid.UUID, reminder_hours: int = 24
    ) -> SMSNotification:
        """Create an SMS reminder for an appointment."""
        # Get appointment details
        result = await self.db.execute(
            select(Appointment, Patient, Clinic)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Clinic, Appointment.clinic_id == Clinic.id)
            .where(Appointment.id == appointment_id)
        )
        appointment, patient, clinic = result.first()

        if not appointment:
            raise ValueError("Appointment not found")

        if not patient.phone:
            raise ValueError("Patient phone number not available")

        # Calculate reminder time
        reminder_time = appointment.start_time - timedelta(hours=reminder_hours)

        # Create SMS notification
        sms_notification = SMSNotification(
            appointment_id=appointment.id,
            patient_id=patient.id,
            clinic_id=clinic.id,
            message_type=SMSNotificationType.APPOINTMENT_REMINDER,
            phone_number=patient.phone,
            message_content=self._generate_reminder_message(
                clinic.name, appointment.start_time, appointment.procedure_name, appointment.dentist_id
            ),
            scheduled_time=reminder_time,
        )

        self.db.add(sms_notification)
        await self.db.commit()
        await self.db.refresh(sms_notification)

        return sms_notification

    async def create_confirmation_notification(
        self, appointment_id: uuid.UUID
    ) -> SMSNotification:
        """Create an SMS confirmation for a newly booked appointment."""
        # Get appointment details
        result = await self.db.execute(
            select(Appointment, Patient, Clinic)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Clinic, Appointment.clinic_id == Clinic.id)
            .where(Appointment.id == appointment_id)
        )
        appointment, patient, clinic = result.first()

        if not appointment:
            raise ValueError("Appointment not found")

        if not patient.phone:
            raise ValueError("Patient phone number not available")

        # Create SMS notification
        sms_notification = SMSNotification(
            appointment_id=appointment.id,
            patient_id=patient.id,
            clinic_id=clinic.id,
            message_type=SMSNotificationType.APPOINTMENT_CONFIRMATION,
            phone_number=patient.phone,
            message_content=self._generate_confirmation_message(
                clinic.name, appointment.start_time, appointment.procedure_name
            ),
            scheduled_time=appointment.created_at,  # Send immediately
        )

        self.db.add(sms_notification)
        await self.db.commit()
        await self.db.refresh(sms_notification)

        return sms_notification

    async def create_move_offer_notification(
        self, appointment_id: uuid.UUID, new_time: datetime, incentive: str
    ) -> SMSNotification:
        """Create an SMS notification for a move offer."""
        # Get appointment details
        result = await self.db.execute(
            select(Appointment, Patient, Clinic)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Clinic, Appointment.clinic_id == Clinic.id)
            .where(Appointment.id == appointment_id)
        )
        appointment, patient, clinic = result.first()

        if not appointment:
            raise ValueError("Appointment not found")

        if not patient.phone:
            raise ValueError("Patient phone number not available")

        # Create SMS notification
        sms_notification = SMSNotification(
            appointment_id=appointment.id,
            patient_id=patient.id,
            clinic_id=clinic.id,
            message_type=SMSNotificationType.MOVE_OFFER,
            phone_number=patient.phone,
            message_content=self._generate_move_offer_message(
                clinic.name, appointment.start_time, new_time, incentive
            ),
            scheduled_time=datetime.utcnow(),  # Send immediately
        )

        self.db.add(sms_notification)
        await self.db.commit()
        await self.db.refresh(sms_notification)

        return sms_notification

    async def get_pending_notifications(self, limit: int = 100) -> List[SMSNotification]:
        """Get pending SMS notifications that are ready to be sent."""
        result = await self.db.execute(
            select(SMSNotification)
            .where(
                and_(
                    SMSNotification.status == SMSNotificationStatus.PENDING,
                    SMSNotification.scheduled_time <= datetime.utcnow(),
                )
            )
            .order_by(SMSNotification.scheduled_time)
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_as_sent(
        self, notification_id: uuid.UUID, provider_message_id: Optional[str] = None
    ) -> SMSNotification:
        """Mark an SMS notification as sent."""
        result = await self.db.execute(
            select(SMSNotification).where(SMSNotification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise ValueError("Notification not found")

        notification.status = SMSNotificationStatus.SENT
        notification.sent_time = datetime.utcnow()
        notification.provider_message_id = provider_message_id

        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def mark_as_failed(
        self, notification_id: uuid.UUID, error_message: str
    ) -> SMSNotification:
        """Mark an SMS notification as failed."""
        result = await self.db.execute(
            select(SMSNotification).where(SMSNotification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise ValueError("Notification not found")

        notification.status = SMSNotificationStatus.FAILED
        notification.error_message = error_message
        notification.retry_count += 1

        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    def _generate_reminder_message(
        self, clinic_name: str, appointment_time: datetime, procedure_name: str, dentist_id: uuid.UUID
    ) -> str:
        """Generate SMS reminder message content."""
        # Get dentist name (would need additional query in real implementation)
        appointment_date = appointment_time.strftime("%A, %B %d, %Y at %I:%M %p")
        return (
            f"Reminder from {clinic_name}: You have an appointment scheduled for "
            f"{appointment_date} for {procedure_name}. "
            f"Please arrive 10 minutes early. Reply STOP to opt out."
        )

    def _generate_confirmation_message(
        self, clinic_name: str, appointment_time: datetime, procedure_name: str
    ) -> str:
        """Generate SMS confirmation message content."""
        appointment_date = appointment_time.strftime("%A, %B %d, %Y at %I:%M %p")
        return (
            f"Thank you for booking with {clinic_name}! "
            f"Your appointment for {procedure_name} is confirmed for "
            f"{appointment_date}. We look forward to seeing you!"
        )

    def _generate_move_offer_message(
        self, clinic_name: str, current_time: datetime, new_time: datetime, incentive: str
    ) -> str:
        """Generate SMS move offer message content."""
        current_date = current_time.strftime("%A, %B %d, %Y at %I:%M %p")
        new_date = new_time.strftime("%A, %B %d, %Y at %I:%M %p")
        return (
            f"{clinic_name}: We have a better time available for your appointment. "
            f"Current: {current_date}. New: {new_date}. "
            f"As a thank you, we're offering {incentive}. "
            f"Reply YES to accept or NO to decline."
        )


# Mock SMS provider for development/testing
class MockSMSProvider:
    """Mock SMS provider for development and testing."""

    async def send_sms(self, phone_number: str, message: str) -> str:
        """Send SMS via mock provider."""
        # In a real implementation, this would call an actual SMS provider API
        # For now, we'll just log and return a mock message ID
        print(f"Mock SMS sent to {phone_number}: {message}")
        return f"mock-msg-{hash(message) % 10000}"


class SMSSenderService:
    """Service for sending SMS notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = SMSNotificationService(db)
        self.sms_provider = MockSMSProvider()

    async def process_pending_notifications(self) -> int:
        """Process all pending SMS notifications."""
        pending_notifications = await self.notification_service.get_pending_notifications()

        sent_count = 0
        for notification in pending_notifications:
            try:
                # Send SMS
                provider_message_id = await self.sms_provider.send_sms(
                    notification.phone_number, notification.message_content
                )

                # Mark as sent
                await self.notification_service.mark_as_sent(notification.id, provider_message_id)
                sent_count += 1

            except Exception as e:
                # Mark as failed
                await self.notification_service.mark_as_failed(notification.id, str(e))

        return sent_count

    async def create_reminder(
        self, request: SMSReminderRequest
    ) -> SMSNotificationResponse:
        """Create an SMS reminder for an appointment."""
        notification = await self.notification_service.create_appointment_reminder(
            request.appointment_id, request.reminder_hours
        )

        return SMSNotificationResponse(
            id=notification.id,
            appointment_id=notification.appointment_id,
            patient_id=notification.patient_id,
            clinic_id=notification.clinic_id,
            message_type=notification.message_type,
            phone_number=notification.phone_number,
            message_content=notification.message_content,
            scheduled_time=notification.scheduled_time,
            status=notification.status,
            created_at=notification.created_at,
        )