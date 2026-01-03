"""
SMS Service for appointment reminders and notifications.
Future enhancement - provides SMS notification capabilities.
"""

from typing import Dict, List


class SMSService:
    """SMS service for sending notifications via SMS."""

    def __init__(self, provider: str = "mock"):
        """
        Initialize SMS service.

        Args:
            provider: SMS provider name (mock, twilio, sns, etc.)
        """
        self.provider = provider
        self.sent_messages: List[Dict] = []

    async def send_appointment_reminder(
        self,
        phone: str,
        appointment_details: Dict,
        hours_before: int = 24
    ) -> bool:
        """
        Send appointment reminder via SMS.

        Args:
            phone: Patient phone number in E.164 format
            appointment_details: Dictionary with appointment information
            hours_before: Hours before appointment to send reminder

        Returns:
            bool: Success status
        """
        # Placeholder for SMS integration
        self.sent_messages.append({
            "type": "reminder",
            "phone": phone,
            "details": appointment_details,
            "hours_before": hours_before
        })
        return True

    async def send_confirmation(self, phone: str, appointment_details: Dict) -> bool:
        """
        Send booking confirmation via SMS.

        Args:
            phone: Patient phone number in E.164 format
            appointment_details: Dictionary with booking confirmation

        Returns:
            bool: Success status
        """
        self.sent_messages.append({
            "type": "confirmation",
            "phone": phone,
            "details": appointment_details
        })
        return True

    async def send_emergency_alert(self, phone: str, priority: str, message: str) -> bool:
        """
        Send emergency alert via SMS.

        Args:
            phone: Patient phone number in E.164 format
            priority: Priority level (URGENT, HIGH, etc.)
            message: Emergency message

        Returns:
            bool: Success status
        """
        self.sent_messages.append({
            "type": "emergency",
            "phone": phone,
            "priority": priority,
            "message": message
        })
        return True

    def get_sent_messages(self) -> List[Dict]:
        """Get list of sent messages."""
        return self.sent_messages

    def clear_messages(self) -> None:
        """Clear sent messages list."""
        self.sent_messages = []
