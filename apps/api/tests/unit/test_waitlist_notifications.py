"""Test waitlist notification service."""

import pytest
from src.services.waitlist_notifications import WaitlistNotificationService


class TestWaitlistNotificationService:
    """Test waitlist notification service functionality."""

    def test_service_initialization(self):
        """Verify service initializes correctly."""
        service = WaitlistNotificationService()
        assert service.notifications == []

    @pytest.mark.asyncio
    async def test_send_slot_available_notification(self):
        """Verify slot available notification is sent correctly."""
        service = WaitlistNotificationService()

        result = await service.send_slot_available_notification(
            waitlist_id="wl_123",
            patient_phone="+61400000000",
            slot_details={"date": "2024-01-15", "time": "10:00"}
        )

        assert result is True
        assert len(service.notifications) == 1
        assert service.notifications[0]["waitlist_id"] == "wl_123"
        assert "available" in service.notifications[0]["message"]

    @pytest.mark.asyncio
    async def test_send_waitlist_confirmation(self):
        """Verify waitlist confirmation is sent correctly."""
        service = WaitlistNotificationService()

        result = await service.send_waitlist_confirmation(
            waitlist_id="wl_123",
            patient_phone="+61400000000",
            appointment_details={"date": "2024-01-15", "time": "10:00"}
        )

        assert result is True
        assert len(service.notifications) == 1
        assert service.notifications[0]["type"] == "confirmation"

    def test_get_notifications(self):
        """Verify getting notifications works correctly."""
        service = WaitlistNotificationService()
        service.notifications = [{"waitlist_id": "wl_123"}]

        notifications = service.get_notifications()
        assert len(notifications) == 1
