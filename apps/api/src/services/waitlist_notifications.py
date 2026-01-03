"""
Waitlist notification service for sending slot availability alerts.
"""

from typing import Dict


class WaitlistNotificationService:
    """Service for waitlist notification management."""

    def __init__(self):
        self.notifications = []

    async def send_slot_available_notification(
        self,
        waitlist_id: str,
        patient_phone: str,
        slot_details: Dict
    ) -> bool:
        """
        Send notification to patient that a slot is available.

        Args:
            waitlist_id: Waitlist entry ID
            patient_phone: Patient phone number
            slot_details: Available slot information

        Returns:
            bool: Success status
        """
        message = (
            f"Good news! A dental appointment slot has become available. "
            f"Date: {slot_details.get('date', 'N/A')} "
            f"Time: {slot_details.get('time', 'N/A')}. "
            f"Reply YES to book or NO to decline."
        )

        self.notifications.append({
            'waitlist_id': waitlist_id,
            'phone': patient_phone,
            'message': message,
            'slot_details': slot_details,
            'sent_at': '2024-01-01T00:00:00'  # Mock timestamp
        })

        return True

    async def send_waitlist_confirmation(
        self,
        waitlist_id: str,
        patient_phone: str,
        appointment_details: Dict
    ) -> bool:
        """
        Send confirmation after patient books from waitlist.

        Args:
            waitlist_id: Waitlist entry ID
            patient_phone: Patient phone number
            appointment_details: Booked appointment info

        Returns:
            bool: Success status
        """
        message = (
            f"Waitlist booking confirmed! "
            f"Date: {appointment_details.get('date', 'N/A')} "
            f"Time: {appointment_details.get('time', 'N/A')}. "
            f"Thank you for your patience."
        )

        self.notifications.append({
            'waitlist_id': waitlist_id,
            'phone': patient_phone,
            'message': message,
            'type': 'confirmation',
            'sent_at': '2024-01-01T00:00:00'  # Mock timestamp
        })

        return True

    def get_notifications(self) -> list:
        """Get all notifications (for testing)."""
        return self.notifications


# Singleton instance
waitlist_notification_service = WaitlistNotificationService()


async def check_and_notify_waitlist(waitlist_id: str, slot_details: Dict) -> bool:
    """
    Check waitlist and notify patients about available slots.

    Args:
        waitlist_id: The waitlist entry ID
        slot_details: Available slot information

    Returns:
        bool: Success status
    """
    # This is a wrapper function for backward compatibility with tests
    # It uses the singleton service instance
    return await waitlist_notification_service.send_slot_available_notification(
        waitlist_id=waitlist_id,
        patient_phone="+61000000000",  # Would be fetched from waitlist entry
        slot_details=slot_details
    )
