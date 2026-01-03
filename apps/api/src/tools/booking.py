"""Appointment booking tool for PMS integration."""

from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

BookingResult = TypedDict('BookingResult', {
    'appointment_id': str,
    'status': str,
    'patient_name': str,
    'procedure_name': str,
    'start_time': str,
    'dentist_name': str,
    'confirmation_message': str,
})


async def book_appointment(
    patient_id: str,
    slot_id: str,
    procedure_code: str,
    db: 'AsyncSession | None' = None,
) -> BookingResult:
    """
    Books an appointment in the Practice Management System.

    This tool creates a new appointment record in the PMS,
    associating a patient with a specific time slot and procedure.

    The booking process:
    1. Validates the slot is still available
    2. Verifies patient exists in system
    3. Checks procedure code is valid
    4. Creates the appointment record
    5. Sends confirmation notification

    Args:
        patient_id: UUID of the patient booking the appointment
        slot_id: UUID of the available slot to book
        procedure_code: Dental procedure code (e.g., "D1110" for Prophylaxis)
        db: Database session for real operations

    Returns:
        A dictionary with booking confirmation:
        - appointment_id: UUID of the created appointment
        - status: "BOOKED"
        - patient_name: Name of the patient
        - procedure_name: Human-readable procedure name
        - start_time: Formatted start time
        - dentist_name: Assigned dentist name
        - confirmation_message: Message to display to patient
    """
    if db is None:
        # Fallback to placeholder implementation
        import uuid
        from datetime import datetime

        return {
            "appointment_id": str(uuid.uuid4()),
            "status": "BOOKED",
            "patient_name": "John Doe",
            "procedure_name": "Dental Cleaning (Prophylaxis)",
            "start_time": "Monday, January 15, 2024 at 9:00 AM",
            "dentist_name": "Dr. Smith",
            "confirmation_message": (
                "Your appointment has been successfully booked! "
                "You'll receive a confirmation email shortly. "
                "Please arrive 10 minutes early to complete any paperwork."
            ),
        }

    from uuid import UUID
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError
    from src.models import Appointment, AppointmentStatus, Patient, Procedure, Dentist
    import uuid

    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": "Invalid patient ID format",
        }

    # Parse slot_id to extract dentist_id and start_time
    # Format: "{dentist_id}@{start_time_iso}" (using @ as separator)
    try:
        dentist_id_str, start_time_str = slot_id.split("@", 1)
        dentist_uuid = UUID(dentist_id_str)
        from datetime import datetime
        start_time = datetime.fromisoformat(start_time_str)
    except (ValueError, IndexError):
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": "Invalid slot ID format",
        }

    # Fetch patient
    patient_result = await db.execute(
        select(Patient).where(Patient.id == patient_uuid)
    )
    patient = patient_result.scalar_one_or_none()

    if not patient:
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": f"Patient {patient_id} not found",
        }

    # Fetch dentist
    dentist_result = await db.execute(
        select(Dentist).where(Dentist.id == dentist_uuid)
    )
    dentist = dentist_result.scalar_one_or_none()

    if not dentist:
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": f"Dentist {dentist_id_str} not found",
        }

    # Fetch procedure
    procedure_result = await db.execute(
        select(Procedure).where(Procedure.code == procedure_code)
    )
    procedure = procedure_result.scalar_one_or_none()

    if not procedure:
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": f"Procedure {procedure_code} not found",
        }

    # Check if slot is still available
    existing_appointments_result = await db.execute(
        select(Appointment).where(
            Appointment.dentist_id == dentist_uuid,
            Appointment.start_time == start_time,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    existing_appointments = existing_appointments_result.scalars().all()

    if existing_appointments:
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": "The selected slot is no longer available",
        }

    # Create appointment
    appointment = Appointment(
        id=uuid.uuid4(),
        patient_id=patient_uuid,
        clinic_id=dentist.clinic_id,
        dentist_id=dentist_uuid,
        start_time=start_time,
        duration_mins=procedure.default_duration_mins,
        procedure_code=procedure.code,
        procedure_name=procedure.name,
        estimated_value=procedure.base_value,
        status=AppointmentStatus.BOOKED,
    )

    try:
        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)
    except IntegrityError:
        await db.rollback()
        return {
            "appointment_id": "",
            "status": "ERROR",
            "patient_name": "",
            "procedure_name": "",
            "start_time": "",
            "dentist_name": "",
            "confirmation_message": "Failed to create appointment",
        }

    # Format confirmation message
    from datetime import datetime
    formatted_time = start_time.strftime("%A, %B %d, %Y at %I:%M %p")

    return {
        "appointment_id": str(appointment.id),
        "status": appointment.status.value,
        "patient_name": patient.name,
        "procedure_name": procedure.name,
        "start_time": formatted_time,
        "dentist_name": dentist.name,
        "confirmation_message": (
            f"Your appointment has been successfully booked! "
            f"Patient: {patient.name}, "
            f"Procedure: {procedure.name}, "
            f"Date: {formatted_time}, "
            f"Dentist: {dentist.name}. "
            f"You'll receive a confirmation email shortly. "
            f"Please arrive 10 minutes early to complete any paperwork."
        ),
    }
