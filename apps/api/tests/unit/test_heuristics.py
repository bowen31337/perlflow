"""Tests for Heuristics API endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


@pytest.mark.asyncio
async def test_calculate_move_score_high_value(client: AsyncClient, async_session: AsyncSession):
    """Test calculating move score for a high-value procedure."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus, Procedure

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe", ltv_score=500.0)
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create existing appointment (low value)
    start_time = datetime.now() + timedelta(days=7)
    appointment = Appointment(
        id=uuid4(),
        patient_id=patient.id,
        clinic_id=clinic.id,
        dentist_id=dentist.id,
        start_time=start_time,
        duration_mins=30,
        procedure_code="D1110",
        procedure_name="Prophylaxis",
        estimated_value=150.0,
        status=AppointmentStatus.BOOKED,
    )
    async_session.add(appointment)
    await async_session.commit()

    # Calculate move score for high-value procedure
    response = await client.post(
        "/heuristics/move-score",
        json={
            "appointment_id": str(appointment.id),
            "candidate_slot": "some-slot",
            "new_procedure_value": 1200.0,  # Crown
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "move_score" in data
    assert "recommendation" in data
    assert "incentive_needed" in data
    assert data["move_score"] > 70  # Should recommend move for high value
    assert data["recommendation"] == "MOVE"


@pytest.mark.asyncio
async def test_calculate_move_score_low_value(client: AsyncClient, async_session: AsyncSession):
    """Test calculating move score for a low-value procedure."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe", ltv_score=500.0)
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create existing appointment (high value)
    start_time = datetime.now() + timedelta(days=7)
    appointment = Appointment(
        id=uuid4(),
        patient_id=patient.id,
        clinic_id=clinic.id,
        dentist_id=dentist.id,
        start_time=start_time,
        duration_mins=60,
        procedure_code="D2710",
        procedure_name="Crown",
        estimated_value=1200.0,
        status=AppointmentStatus.BOOKED,
    )
    async_session.add(appointment)
    await async_session.commit()

    # Calculate move score for low-value procedure
    response = await client.post(
        "/heuristics/move-score",
        json={
            "appointment_id": str(appointment.id),
            "candidate_slot": "some-slot",
            "new_procedure_value": 150.0,  # Cleaning
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["recommendation"] == "KEEP"


@pytest.mark.asyncio
async def test_calculate_move_score_invalid_appointment(client: AsyncClient):
    """Test calculating move score for non-existent appointment."""
    response = await client.post(
        "/heuristics/move-score",
        json={
            "appointment_id": str(uuid4()),
            "candidate_slot": "some-slot",
            "new_procedure_value": 1000.0,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_calculate_move_score_invalid_format(client: AsyncClient):
    """Test calculating move score with invalid appointment_id format."""
    response = await client.post(
        "/heuristics/move-score",
        json={
            "appointment_id": "not-a-uuid",
            "candidate_slot": "some-slot",
            "new_procedure_value": 1000.0,
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_optimize_day_with_suggestions(client: AsyncClient, async_session: AsyncSession):
    """Test day optimization returns suggestions for high-value procedures."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus, Procedure

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe", ltv_score=100.0)

    # Create procedures
    cleaning = Procedure(
        id=uuid4(), code="D1110", name="Prophylaxis", category="Preventive",
        default_duration_mins=30, base_value=150.0, priority_weight=0.3
    )
    crown = Procedure(
        id=uuid4(), code="D2710", name="Crown", category="Restorative",
        default_duration_mins=90, base_value=1200.0, priority_weight=0.8
    )

    async_session.add_all([clinic, dentist, patient, cleaning, crown])
    await async_session.commit()

    # Create existing low-value appointment
    test_date = datetime.now().date() + timedelta(days=7)
    start_time = datetime.combine(test_date, datetime.min.time()).replace(hour=10)
    appointment = Appointment(
        id=uuid4(),
        patient_id=patient.id,
        clinic_id=clinic.id,
        dentist_id=dentist.id,
        start_time=start_time,
        duration_mins=30,
        procedure_code="D1110",
        procedure_name="Prophylaxis",
        estimated_value=150.0,
        status=AppointmentStatus.BOOKED,
    )
    async_session.add(appointment)
    await async_session.commit()

    # Optimize day
    response = await client.post(
        "/heuristics/optimize-day",
        json={
            "clinic_id": str(clinic.id),
            "date": test_date.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    # Should have suggestions since we have a low-value appointment and high-value procedure available


@pytest.mark.asyncio
async def test_optimize_day_no_appointments(client: AsyncClient, async_session: AsyncSession):
    """Test day optimization with no appointments."""
    from src.models import Clinic

    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    async_session.add(clinic)
    await async_session.commit()

    test_date = datetime.now().date() + timedelta(days=7)
    response = await client.post(
        "/heuristics/optimize-day",
        json={
            "clinic_id": str(clinic.id),
            "date": test_date.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["suggestions"] == []


@pytest.mark.asyncio
async def test_optimize_day_invalid_clinic(client: AsyncClient):
    """Test day optimization with invalid clinic_id."""
    test_date = datetime.now().date() + timedelta(days=7)
    response = await client.post(
        "/heuristics/optimize-day",
        json={
            "clinic_id": str(uuid4()),
            "date": test_date.isoformat(),
        },
    )

    assert response.status_code == 200  # Returns empty suggestions, not error
    data = response.json()
    assert data["suggestions"] == []
