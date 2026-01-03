"""Tests for Admin API endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_analytics_empty_db(client: AsyncClient):
    """Test analytics endpoint with empty database."""
    response = await client.get("/admin/analytics")

    assert response.status_code == 200
    data = response.json()
    assert "no_show_rate" in data
    assert "chair_utilization" in data
    assert "revenue_optimization" in data
    assert "move_acceptance_rate" in data
    assert "average_triage_accuracy" in data


@pytest.mark.asyncio
async def test_get_analytics_with_data(client: AsyncClient, async_session: AsyncSession):
    """Test analytics endpoint with some data."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus, Procedure

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    procedure = Procedure(
        id=uuid4(), code="D1110", name="Prophylaxis", category="Preventive",
        default_duration_mins=30, base_value=150.0, priority_weight=0.3
    )
    async_session.add_all([clinic, dentist, patient, procedure])
    await async_session.commit()

    # Create appointments (some booked, some cancelled)
    for i in range(3):
        appointment = Appointment(
            id=uuid4(),
            patient_id=patient.id,
            clinic_id=clinic.id,
            dentist_id=dentist.id,
            start_time=datetime.now() + timedelta(days=i+1),
            duration_mins=30,
            procedure_code="D1110",
            procedure_name="Prophylaxis",
            estimated_value=150.0,
            status=AppointmentStatus.BOOKED if i < 2 else AppointmentStatus.CANCELLED,
        )
        async_session.add(appointment)
    await async_session.commit()

    response = await client.get("/admin/analytics")

    assert response.status_code == 200
    data = response.json()
    assert data["no_show_rate"] == 33.33  # 1 cancelled out of 3
    assert data["chair_utilization"] > 0
    assert data["revenue_optimization"]["current_month"] == 300.0  # 2 * 150


@pytest.mark.asyncio
async def test_get_pending_feedback_empty(client: AsyncClient):
    """Test pending feedback endpoint with no feedback."""
    response = await client.get("/admin/feedback/pending")

    assert response.status_code == 200
    data = response.json()
    assert data["feedback_items"] == []


@pytest.mark.asyncio
async def test_get_pending_feedback_with_data(client: AsyncClient, async_session: AsyncSession):
    """Test pending feedback endpoint with unapproved feedback."""
    from src.models import Patient, Feedback

    # Create patient
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add(patient)
    await async_session.commit()

    # Create unapproved feedback
    feedback = Feedback(
        id=uuid4(),
        patient_id=patient.id,
        rating=5,
        content="Great service!",
        is_approved=False,
        created_at=datetime.now(),
    )
    async_session.add(feedback)
    await async_session.commit()

    response = await client.get("/admin/feedback/pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data["feedback_items"]) == 1
    assert data["feedback_items"][0]["patient_name"] == "John Doe"
    assert data["feedback_items"][0]["rating"] == 5
    assert data["feedback_items"][0]["content"] == "Great service!"


@pytest.mark.asyncio
async def test_get_pending_feedback_only_unapproved(client: AsyncClient, async_session: AsyncSession):
    """Test that only unapproved feedback is returned."""
    from src.models import Patient, Feedback

    # Create patient
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add(patient)
    await async_session.commit()

    # Create approved feedback
    approved_feedback = Feedback(
        id=uuid4(),
        patient_id=patient.id,
        rating=5,
        content="Already approved",
        is_approved=True,
        created_at=datetime.now(),
        approved_at=datetime.now(),
        approved_by=uuid4(),
    )
    # Create unapproved feedback
    unapproved_feedback = Feedback(
        id=uuid4(),
        patient_id=patient.id,
        rating=4,
        content="Pending approval",
        is_approved=False,
        created_at=datetime.now(),
    )
    async_session.add_all([approved_feedback, unapproved_feedback])
    await async_session.commit()

    response = await client.get("/admin/feedback/pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data["feedback_items"]) == 1
    assert data["feedback_items"][0]["content"] == "Pending approval"


@pytest.mark.asyncio
async def test_approve_feedback_success(client: AsyncClient, async_session: AsyncSession):
    """Test approving a feedback item successfully."""
    from src.models import Patient, Feedback

    # Create patient
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add(patient)
    await async_session.commit()

    # Create unapproved feedback
    feedback = Feedback(
        id=uuid4(),
        patient_id=patient.id,
        rating=5,
        content="Great service!",
        is_approved=False,
        created_at=datetime.now(),
    )
    async_session.add(feedback)
    await async_session.commit()

    response = await client.put(f"/admin/feedback/{feedback.id}/approve")

    assert response.status_code == 200
    data = response.json()
    assert data["is_approved"] is True
    assert data["approved_by"] is not None
    assert data["approved_at"] is not None


@pytest.mark.asyncio
async def test_approve_feedback_not_found(client: AsyncClient):
    """Test approving non-existent feedback returns 404."""
    response = await client.put(f"/admin/feedback/{uuid4()}/approve")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_feedback_already_approved(client: AsyncClient, async_session: AsyncSession):
    """Test approving already approved feedback returns 400."""
    from src.models import Patient, Feedback

    # Create patient
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add(patient)
    await async_session.commit()

    # Create approved feedback
    feedback = Feedback(
        id=uuid4(),
        patient_id=patient.id,
        rating=5,
        content="Already approved",
        is_approved=True,
        created_at=datetime.now(),
        approved_at=datetime.now(),
        approved_by=uuid4(),
    )
    async_session.add(feedback)
    await async_session.commit()

    response = await client.put(f"/admin/feedback/{feedback.id}/approve")

    assert response.status_code == 400
    assert "already approved" in response.json()["detail"].lower()
