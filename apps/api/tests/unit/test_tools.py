"""Tests for tool functions (availability, heuristics, booking, offers)."""

import pytest
from sqlalchemy import select
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from src.tools.availability import check_availability
from src.tools.heuristics import heuristic_move_check
from src.tools.booking import book_appointment
from src.tools.offers import send_move_offer
from src.models import (
    Clinic, Dentist, Patient, Appointment, AppointmentStatus,
    Procedure, MoveOffer, MoveOfferStatus
)


@pytest.mark.asyncio
async def test_check_availability_no_db():
    """Test check_availability without database returns placeholder."""
    result = await check_availability("2024-01-15T09:00:00", "2024-01-17T17:00:00")
    assert "Available slots" in result
    assert "Dr. Smith" in result


@pytest.mark.asyncio
async def test_check_availability_with_db(async_session: AsyncSession):
    """Test check_availability with database returns real slots."""
    # Create clinic and dentist
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    async_session.add_all([clinic, dentist])
    await async_session.commit()

    start = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0).isoformat()
    end = (datetime.now() + timedelta(days=2)).replace(hour=17, minute=0).isoformat()

    result = await check_availability(start, end, async_session, str(clinic.id))
    assert "Available slots" in result


@pytest.mark.asyncio
async def test_check_availability_no_dentists(async_session: AsyncSession):
    """Test check_availability with no dentists."""
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    async_session.add(clinic)
    await async_session.commit()

    start = (datetime.now() + timedelta(days=1)).isoformat()
    end = (datetime.now() + timedelta(days=2)).isoformat()

    result = await check_availability(start, end, async_session, str(clinic.id))
    assert "No active dentists" in result


@pytest.mark.asyncio
async def test_heuristic_move_check_no_db():
    """Test heuristic_move_check without database."""
    result = await heuristic_move_check(str(uuid4()), 1000.0)
    assert "move_score" in result
    assert "recommendation" in result
    assert "incentive_needed" in result
    assert "revenue_difference" in result


@pytest.mark.asyncio
async def test_heuristic_move_check_with_db(async_session: AsyncSession):
    """Test heuristic_move_check with database."""
    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe", ltv_score=500.0)
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create appointment
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

    result = await heuristic_move_check(str(appointment.id), 1000.0, async_session)
    assert result["move_score"] > 0
    assert result["revenue_difference"] > 0


@pytest.mark.asyncio
async def test_heuristic_move_check_invalid_appointment(async_session: AsyncSession):
    """Test heuristic_move_check with invalid appointment_id."""
    result = await heuristic_move_check(str(uuid4()), 1000.0, async_session)
    assert result["move_score"] == 0
    assert result["recommendation"] == "KEEP"


@pytest.mark.asyncio
async def test_book_appointment_no_db():
    """Test book_appointment without database."""
    result = await book_appointment(str(uuid4()), "slot-id", "D1110")
    assert result["status"] == "BOOKED"
    assert "appointment_id" in result


@pytest.mark.asyncio
async def test_book_appointment_with_db(async_session: AsyncSession):
    """Test book_appointment with database."""
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

    # Create slot_id
    start_time = datetime.now() + timedelta(days=7)
    slot_id = f"{dentist.id}@{start_time.isoformat()}"

    result = await book_appointment(
        str(patient.id),
        slot_id,
        "D1110",
        async_session
    )
    assert result["status"] == "BOOKED"
    assert result["patient_name"] == "John Doe"


@pytest.mark.asyncio
async def test_book_appointment_invalid_patient(async_session: AsyncSession):
    """Test book_appointment with invalid patient_id."""
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    async_session.add_all([clinic, dentist])
    await async_session.commit()

    start_time = datetime.now() + timedelta(days=7)
    slot_id = f"{dentist.id}@{start_time.isoformat()}"

    result = await book_appointment(
        str(uuid4()),
        slot_id,
        "D1110",
        async_session
    )
    assert result["status"] == "ERROR"


@pytest.mark.asyncio
async def test_book_appointment_slot_taken(async_session: AsyncSession):
    """Test book_appointment when slot is already taken."""
    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient1 = Patient(id=uuid4(), phone="+61411111111", name="Patient 1")
    patient2 = Patient(id=uuid4(), phone="+61422222222", name="Patient 2")
    procedure = Procedure(
        id=uuid4(), code="D1110", name="Prophylaxis", category="Preventive",
        default_duration_mins=30, base_value=150.0, priority_weight=0.3
    )
    async_session.add_all([clinic, dentist, patient1, patient2, procedure])
    await async_session.commit()

    # Create existing appointment
    start_time = datetime.now() + timedelta(days=7)
    appointment = Appointment(
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
    async_session.add(appointment)
    await async_session.commit()

    slot_id = f"{dentist.id}@{start_time.isoformat()}"

    result = await book_appointment(
        str(patient2.id),
        slot_id,
        "D1110",
        async_session
    )
    assert result["status"] == "ERROR"
    assert "no longer available" in result["confirmation_message"]


@pytest.mark.asyncio
async def test_send_move_offer_no_db():
    """Test send_move_offer without database."""
    result = await send_move_offer(str(uuid4()), "new-slot", "10% discount")
    assert result["status"] == "PENDING"
    assert "offer_id" in result


@pytest.mark.asyncio
async def test_send_move_offer_with_db(async_session: AsyncSession):
    """Test send_move_offer with database."""
    # Create entities
    clinic = Clinic(id=uuid4(), name="Test Clinic", api_key="test_key", timezone="Australia/Sydney", settings={})
    dentist = Dentist(id=uuid4(), clinic_id=clinic.id, name="Dr. Test", is_active=True, specializations=["general"], schedule={})
    patient = Patient(id=uuid4(), phone="+61412345678", name="John Doe")
    async_session.add_all([clinic, dentist, patient])
    await async_session.commit()

    # Create appointment
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

    result = await send_move_offer(
        str(appointment.id),
        "new-slot-id",
        "10% discount",
        async_session
    )
    assert result["status"] == "PENDING"
    assert result["incentive"] == "10% discount"

    # Verify offer was created in database
    offer_result = await async_session.execute(
        select(MoveOffer).where(MoveOffer.original_appointment_id == appointment.id)
    )
    offer = offer_result.scalar_one_or_none()
    assert offer is not None
    assert offer.status == MoveOfferStatus.PENDING


@pytest.mark.asyncio
async def test_send_move_offer_invalid_appointment(async_session: AsyncSession):
    """Test send_move_offer with invalid appointment_id."""
    result = await send_move_offer(
        str(uuid4()),
        "new-slot",
        "10% discount",
        async_session
    )
    assert result["status"] == "ERROR"
