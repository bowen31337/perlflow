"""Tests for Appointments API endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_available_slots(client: AsyncClient, async_session: AsyncSession):
    """Test retrieving available appointment slots."""
    from src.models import Clinic, Dentist
    from sqlalchemy import select

    # Create clinic
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={"operating_hours": {"start": "09:00", "end": "17:00"}},
    )
    async_session.add(clinic)

    # Create dentist
    dentist = Dentist(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Dr. Smith",
        is_active=True,
        specializations=["general"],
        schedule={"monday": True, "tuesday": True, "wednesday": True, "thursday": True, "friday": True},
    )
    async_session.add(dentist)
    await async_session.commit()

    # Get available slots for next week
    start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    response = await client.get(
        f"/appointments/available?clinic_id={clinic.id}&date_range={start_date}/{end_date}",
    )

    assert response.status_code == 200
    data = response.json()
    assert "slots" in data
    assert len(data["slots"]) > 0

    # Check slot structure
    slot = data["slots"][0]
    assert "id" in slot
    assert "start_time" in slot
    assert "end_time" in slot
    assert "dentist_id" in slot
    assert "dentist_name" in slot
    assert slot["dentist_name"] == "Dr. Smith"


@pytest.mark.asyncio
async def test_get_available_slots_filters_by_procedure(client: AsyncClient, async_session: AsyncSession):
    """Test filtering available slots by procedure code."""
    from src.models import Clinic, Dentist, Procedure
    from sqlalchemy import select

    # Create clinic and dentist
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={"operating_hours": {"start": "09:00", "end": "17:00"}},
    )
    async_session.add(clinic)

    dentist = Dentist(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Dr. Jones",
        is_active=True,
        specializations=["general"],
        schedule={"monday": True, "tuesday": True},
    )
    async_session.add(dentist)

    # Create procedure with 60 min duration
    procedure = Procedure(
        id=uuid4(),
        code="D2710",  # Crown
        name="Crown - Porcelain Fused to Metal",
        category="Restorative",
        default_duration_mins=60,
        base_value=1200.0,
        priority_weight=0.8,
    )
    async_session.add(procedure)
    await async_session.commit()

    # Get slots with procedure filter
    start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    response = await client.get(
        f"/appointments/available?clinic_id={clinic.id}&date_range={start_date}/{end_date}&procedure_code=D2710",
    )

    assert response.status_code == 200
    data = response.json()
    assert "slots" in data

    # Slots should be 60 minutes apart
    if len(data["slots"]) > 1:
        slot1 = datetime.fromisoformat(data["slots"][0]["start_time"])
        slot2 = datetime.fromisoformat(data["slots"][1]["start_time"])
        diff = (slot2 - slot1).total_seconds() / 60
        assert diff == 60.0


@pytest.mark.asyncio
async def test_get_available_slots_clinic_not_found(client: AsyncClient):
    """Test getting slots for non-existent clinic returns 404."""
    start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    response = await client.get(
        f"/appointments/available?clinic_id={uuid4()}&date_range={start_date}/{end_date}",
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_available_slots_invalid_date_range(client: AsyncClient, async_session: AsyncSession):
    """Test getting slots with invalid date range returns 400."""
    from src.models import Clinic
    from sqlalchemy import select

    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={},
    )
    async_session.add(clinic)
    await async_session.commit()

    response = await client.get(
        f"/appointments/available?clinic_id={clinic.id}&date_range=invalid",
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_appointment_success(client: AsyncClient, async_session: AsyncSession):
    """Test creating a new appointment successfully."""
    from src.models import Clinic, Dentist, Patient, Procedure
    from sqlalchemy import select

    # Create clinic, dentist, patient, procedure
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={},
    )
    async_session.add(clinic)

    dentist = Dentist(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Dr. Test",
        is_active=True,
        specializations=["general"],
        schedule={"monday": True},
    )
    async_session.add(dentist)

    patient = Patient(
        id=uuid4(),
        phone="+61412345678",
        name="John Doe",
    )
    async_session.add(patient)

    procedure = Procedure(
        id=uuid4(),
        code="D1110",
        name="Prophylaxis",
        category="Preventive",
        default_duration_mins=30,
        base_value=150.0,
        priority_weight=0.3,
    )
    async_session.add(procedure)

    # Create a session for this clinic
    from src.models import AgentSession, SessionStatus
    session = AgentSession(
        session_id=uuid4(),
        patient_id=patient.id,
        clinic_id=clinic.id,
        current_node="Receptionist",
        messages=[],
        status=SessionStatus.ACTIVE,
    )
    async_session.add(session)

    await async_session.commit()

    # Create a slot_id manually
    start_time = (datetime.now() + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
    slot_id = f"{dentist.id}@{start_time.isoformat()}"

    response = await client.post(
        "/appointments",
        json={
            "session_id": str(session.session_id),  # Use actual session ID
            "patient_id": str(patient.id),
            "slot_id": slot_id,
            "procedure_code": "D1110",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == str(patient.id)
    assert data["clinic_id"] == str(clinic.id)
    assert data["dentist_id"] == str(dentist.id)
    assert data["procedure_code"] == "D1110"
    assert data["status"] == "BOOKED"
    assert data["estimated_value"] == 150.0


@pytest.mark.asyncio
async def test_create_appointment_double_booking(client: AsyncClient, async_session: AsyncSession):
    """Test that double-booking the same slot returns 409."""
    from src.models import Clinic, Dentist, Patient, Procedure, Appointment, AppointmentStatus, AgentSession, SessionStatus
    from uuid import uuid4

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient1 = Patient(id=uuid4(), phone="+61411111111", name="Patient 1")
    patient2 = Patient(id=uuid4(), phone="+61422222222", name="Patient 2")
    procedure = Procedure(id=uuid4(), code="D1110", name="Prophylaxis", category="Preventive", default_duration_mins=30, base_value=150.0, priority_weight=0.3)

    async_session.add_all([clinic, dentist, patient1, patient2, procedure])
    await async_session.commit()

    # Create a session
    session = AgentSession(
        session_id=uuid4(),
        patient_id=patient1.id,
        clinic_id=clinic.id,
        current_node="Receptionist",
        messages=[],
        status=SessionStatus.ACTIVE,
    )
    async_session.add(session)
    await async_session.commit()

    # Create existing appointment
    start_time = (datetime.now() + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
    existing_appt = Appointment(
        id=uuid4(),
        patient_id=patient1.id,
        clinic_id=clinic.id,
        dentist_id=dentist.id,
        start_time=start_time,
        duration_mins=30,
        procedure_code="D1110",
        procedure_name="Prophylaxis",
        estimated_value=150.0,
        status=AppointmentStatus.BOOKED,
    )
    async_session.add(existing_appt)
    await async_session.commit()

    # Try to book same slot
    slot_id = f"{dentist.id}@{start_time.isoformat()}"
    response = await client.post(
        "/appointments",
        json={
            "session_id": str(session.session_id),
            "patient_id": str(patient2.id),
            "slot_id": slot_id,
            "procedure_code": "D1110",
        },
    )

    assert response.status_code == 409
    assert "no longer available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_appointment_status(client: AsyncClient, async_session: AsyncSession):
    """Test updating an appointment's status."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus
    from uuid import uuid4

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create appointment
    appointment = Appointment(
        id=uuid4(),
        patient_id=patient.id,
        clinic_id=clinic.id,
        dentist_id=dentist.id,
        start_time=datetime.now() + timedelta(days=7),
        duration_mins=30,
        procedure_code="D1110",
        procedure_name="Prophylaxis",
        estimated_value=150.0,
        status=AppointmentStatus.BOOKED,
    )
    async_session.add(appointment)
    await async_session.commit()

    # Update status to CANCELLED
    response = await client.put(
        f"/appointments/{appointment.id}",
        json={"status": "CANCELLED"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_update_appointment_time(client: AsyncClient, async_session: AsyncSession):
    """Test updating an appointment's time."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus
    from uuid import uuid4

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create appointment at 10:00
    start_time = (datetime.now() + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
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

    # Move to 11:00
    new_time = start_time + timedelta(hours=1)
    response = await client.put(
        f"/appointments/{appointment.id}",
        json={"start_time": new_time.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()
    assert datetime.fromisoformat(data["start_time"]) == new_time


@pytest.mark.asyncio
async def test_update_appointment_not_found(client: AsyncClient):
    """Test updating a non-existent appointment returns 404."""
    response = await client.put(
        f"/appointments/{uuid4()}",
        json={"status": "CANCELLED"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_appointment(client: AsyncClient, async_session: AsyncSession):
    """Test cancelling an appointment returns 204."""
    from src.models import Clinic, Dentist, Patient, Appointment, AppointmentStatus
    from uuid import uuid4

    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create appointment
    appointment = Appointment(
        id=uuid4(),
        patient_id=patient.id,
        clinic_id=clinic.id,
        dentist_id=dentist.id,
        start_time=datetime.now() + timedelta(days=7),
        duration_mins=30,
        procedure_code="D1110",
        procedure_name="Prophylaxis",
        estimated_value=150.0,
        status=AppointmentStatus.BOOKED,
    )
    async_session.add(appointment)
    await async_session.commit()

    # Cancel appointment
    response = await client.delete(f"/appointments/{appointment.id}")

    assert response.status_code == 204

    # Verify status in database
    await async_session.refresh(appointment)
    assert appointment.status == AppointmentStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_appointment_not_found(client: AsyncClient):
    """Test cancelling a non-existent appointment returns 404."""
    response = await client.delete(f"/appointments/{uuid4()}")

    assert response.status_code == 404

import sys
