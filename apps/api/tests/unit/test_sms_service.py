"""Test SMS notification service."""

import pytest
from src.services.sms_service import SMSService


class TestSMSService:
    """Test SMS service functionality."""

    def test_sms_service_initialization(self):
        """Verify SMS service initializes correctly."""
        service = SMSService(provider="mock")
        assert service.provider == "mock"
        assert service.sent_messages == []

    @pytest.mark.asyncio
    async def test_send_appointment_reminder(self):
        """Verify appointment reminder SMS is sent correctly."""
        service = SMSService(provider="mock")

        appointment_details = {
            "id": "apt_123",
            "date": "2024-01-15",
            "time": "10:00",
            "procedure": "Cleaning"
        }

        result = await service.send_appointment_reminder(
            phone="+61400000000",
            appointment_details=appointment_details,
            hours_before=24
        )

        assert result is True
        assert len(service.sent_messages) == 1
        assert service.sent_messages[0]["type"] == "reminder"
        assert service.sent_messages[0]["phone"] == "+61400000000"

    @pytest.mark.asyncio
    async def test_send_confirmation(self):
        """Verify appointment confirmation SMS is sent correctly."""
        service = SMSService(provider="mock")

        appointment_details = {
            "id": "apt_456",
            "date": "2024-01-20",
            "time": "14:30",
            "procedure": "Root Canal"
        }

        result = await service.send_confirmation(
            phone="+61400000000",
            appointment_details=appointment_details
        )

        assert result is True
        assert len(service.sent_messages) == 1
        assert service.sent_messages[0]["type"] == "confirmation"

    @pytest.mark.asyncio
    async def test_send_emergency_alert(self):
        """Verify emergency alert SMS is sent correctly."""
        service = SMSService(provider="mock")

        result = await service.send_emergency_alert(
            phone="+61400000000",
            priority="URGENT",
            message="Please call immediately"
        )

        assert result is True
        assert len(service.sent_messages) == 1
        assert service.sent_messages[0]["type"] == "emergency"
        assert service.sent_messages[0]["priority"] == "URGENT"
        assert service.sent_messages[0]["message"] == "Please call immediately"

    def test_get_sent_messages(self):
        """Verify getting sent messages works correctly."""
        service = SMSService(provider="mock")
        service.sent_messages = [{"type": "test"}]

        messages = service.get_sent_messages()
        assert len(messages) == 1

    def test_clear_messages(self):
        """Verify clearing messages works correctly."""
        service = SMSService(provider="mock")
        service.sent_messages = [{"type": "test"}]

        service.clear_messages()
        assert len(service.sent_messages) == 0
