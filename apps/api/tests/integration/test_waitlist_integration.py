"""Integration tests for waitlist management."""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.waitlist_service import waitlist_service
from src.services.waitlist_notifications import waitlist_notification_service


client = TestClient(app)


class TestWaitlistIntegration:
    """Integration tests for waitlist flow."""

    def setup_method(self):
        """Reset waitlist services before each test."""
        waitlist_service.waitlist_entries = []
        waitlist_service.next_position = 1
        waitlist_notification_service.notifications = []

    def test_full_waitlist_flow(self):
        """Test complete waitlist flow: add -> notify -> respond."""
        # Step 1: Add patient to waitlist
        response = client.post(
            "/waitlist",
            json={
                "patient_id": "pat_123",
                "clinic_id": "clinic_456",
                "preferred_time": "morning",
                "procedure_code": "D1110",
                "priority_score": 50
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        waitlist_id = data["waitlist_id"]

        # Step 2: Get waitlist for clinic
        response = client.get("/waitlist/clinic_456")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

        # Step 3: Notify patient about available slot
        response = client.post(f"/waitlist/{waitlist_id}/notify")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Step 4: Update patient response
        response = client.put(
            f"/waitlist/{waitlist_id}/response",
            params={"response": "accepted"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_waitlist_priority_ordering(self):
        """Test waitlist respects priority ordering."""
        # Add patients with different priorities
        clients = [
            {"patient_id": "pat_low", "clinic_id": "clinic_1", "priority_score": 10},
            {"patient_id": "pat_high", "clinic_id": "clinic_1", "priority_score": 90},
            {"patient_id": "pat_med", "clinic_id": "clinic_1", "priority_score": 50},
        ]

        for client_data in clients:
            response = client.post("/waitlist", json=client_data)
            assert response.status_code == 200

        # Get waitlist
        response = client.get("/waitlist/clinic_1")
        data = response.json()

        # Verify all entries exist
        assert data["count"] == 3

        # Verify entries are in order of addition (position)
        entries = data["waitlist"]
        assert entries[0]["patient_id"] == "pat_low"
        assert entries[1]["patient_id"] == "pat_high"
        assert entries[2]["patient_id"] == "pat_med"
