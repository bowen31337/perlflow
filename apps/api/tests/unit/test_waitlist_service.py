"""Test waitlist service."""

import pytest
from src.services.waitlist_service import WaitlistService


class TestWaitlistService:
    """Test waitlist service functionality."""

    def test_waitlist_service_initialization(self):
        """Verify waitlist service initializes correctly."""
        service = WaitlistService()
        assert service.waitlist_entries == []
        assert service.next_position == 1

    @pytest.mark.asyncio
    async def test_add_to_waitlist(self):
        """Verify adding patient to waitlist works correctly."""
        service = WaitlistService()

        result = await service.add_to_waitlist(
            patient_id="pat_123",
            clinic_id="clinic_456",
            preferred_date_range={"start": "2024-01-15", "end": "2024-01-20"},
            preferred_time="morning",
            procedure_code="D1110",
            priority_score=50
        )

        assert result["waitlist_id"] is not None
        assert result["position"] == 1
        assert len(service.waitlist_entries) == 1

    @pytest.mark.asyncio
    async def test_get_waitlist_by_clinic(self):
        """Verify getting waitlist by clinic works correctly."""
        service = WaitlistService()

        await service.add_to_waitlist(
            patient_id="pat_123",
            clinic_id="clinic_456"
        )

        entries = await service.get_waitlist_by_clinic("clinic_456")
        assert len(entries) == 1
        assert entries[0]["patient_id"] == "pat_123"

    @pytest.mark.asyncio
    async def test_notify_patient(self):
        """Verify notifying patient works correctly."""
        service = WaitlistService()

        result = await service.add_to_waitlist(
            patient_id="pat_123",
            clinic_id="clinic_456"
        )

        success = await service.notify_patient(result["waitlist_id"])
        assert success is True

        entry = service.waitlist_entries[0]
        assert entry["notified"] is True

    @pytest.mark.asyncio
    async def test_update_response(self):
        """Verify updating patient response works correctly."""
        service = WaitlistService()

        result = await service.add_to_waitlist(
            patient_id="pat_123",
            clinic_id="clinic_456"
        )

        success = await service.update_response(result["waitlist_id"], "accepted")
        assert success is True

        entry = service.waitlist_entries[0]
        assert entry["response"] == "accepted"
        assert entry["status"] == "filled"
