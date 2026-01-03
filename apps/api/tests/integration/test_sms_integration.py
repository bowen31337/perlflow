"""Integration tests for SMS notifications."""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.sms_service import sms_service


client = TestClient(app)


class TestSMSIntegration:
    """Integration tests for SMS notification flow."""

    def setup_method(self):
        """Reset SMS service before each test."""
        sms_service.clear_messages()

    def test_full_sms_reminder_flow(self):
        """Test complete SMS reminder notification flow."""
        # Step 1: Send notification request
        response = client.post(
            "/notifications/send",
            json={
                "phone": "+61400000000",
                "type": "reminder",
                "appointment_details": {
                    "id": "apt_123",
                    "date": "2024-01-15",
                    "time": "10:00",
                    "procedure": "Cleaning"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Step 2: Verify SMS was sent
        messages = sms_service.get_sent_messages()
        assert len(messages) == 1
        assert messages[0]["type"] == "reminder"
        assert "+61400000000" in messages[0]["phone"]

    def test_full_sms_confirmation_flow(self):
        """Test complete SMS confirmation flow."""
        response = client.post(
            "/notifications/send",
            json={
                "phone": "+61400000000",
                "type": "confirmation",
                "appointment_details": {
                    "id": "apt_456",
                    "date": "2024-01-20",
                    "time": "14:30",
                    "procedure": "Root Canal"
                }
            }
        )

        assert response.status_code == 200

        messages = sms_service.get_sent_messages()
        assert len(messages) == 1
        assert messages[0]["type"] == "confirmation"

    def test_multiple_notifications(self):
        """Test sending multiple notifications."""
        # Send multiple notifications
        for i in range(3):
            response = client.post(
                "/notifications/send",
                json={
                    "phone": f"+6140000000{i}",
                    "type": "reminder",
                    "appointment_details": {"id": f"apt_{i}"}
                }
            )
            assert response.status_code == 200

        # Verify all were sent
        messages = sms_service.get_sent_messages()
        assert len(messages) == 3
