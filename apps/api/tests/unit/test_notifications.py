"""Test notification API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestNotificationEndpoints:
    """Test notification API endpoints."""

    def test_send_notification_reminder(self):
        """Test sending appointment reminder notification."""
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
        assert "message_id" in data

    def test_send_notification_confirmation(self):
        """Test sending appointment confirmation notification."""
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
        data = response.json()
        assert data["success"] is True

    def test_send_notification_emergency(self):
        """Test sending emergency notification."""
        response = client.post(
            "/notifications/send",
            json={
                "phone": "+61400000000",
                "type": "emergency",
                "priority": "URGENT",
                "message": "Please call immediately"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_send_notification_invalid_type(self):
        """Test sending notification with invalid type."""
        response = client.post(
            "/notifications/send",
            json={
                "phone": "+61400000000",
                "type": "invalid_type"
            }
        )
        assert response.status_code == 400

    def test_get_notification_status(self):
        """Test getting notification status."""
        response = client.get("/notifications/status/msg_123")
        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == "msg_123"
        assert data["status"] == "delivered"

    def test_get_notification_history(self):
        """Test getting notification history."""
        # First send a notification
        client.post(
            "/notifications/send",
            json={
                "phone": "+61400000000",
                "type": "reminder",
                "appointment_details": {"id": "apt_123"}
            }
        )

        # Then get history
        response = client.get("/notifications/history")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["messages"]) >= 1
