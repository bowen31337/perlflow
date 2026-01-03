"""Appointments API routes."""

from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.models import Appointment, AppointmentStatus, Clinic, Dentist, Patient, Procedure

router = APIRouter()


class SlotResponse(BaseModel):
    """Response model for an available slot."""

    id: str
    start_time: datetime
    end_time: datetime
    dentist_id: str
    dentist_name: str


class AvailableSlotsResponse(BaseModel):
    """Response model for available slots."""

    slots: list[SlotResponse]


class CreateAppointmentRequest(BaseModel):
    """Request model for creating an appointment."""

    session_id: str
    patient_id: str
    slot_id: str
    procedure_code: str = Field(..., description="Dental procedure code (e.g., D1110)")


class AppointmentResponse(BaseModel):
    """Response model for an appointment."""

    id: str
    patient_id: str
    clinic_id: str
    dentist_id: str
    start_time: datetime
    duration_mins: int
    procedure_code: str
    procedure_name: str
    estimated_value: float
    status: str


class UpdateAppointmentRequest(BaseModel):
    """Request model for updating an appointment."""

    status: str | None = None
    start_time: datetime | None = None


@router.get(
    "/available",
    response_model=AvailableSlotsResponse,
    summary="Get available appointment slots",
    description="Retrieves available appointment slots for a clinic within a date range.",
)
async def get_available_slots(
    clinic_id: Annotated[UUID, Query(description="Clinic UUID")],
    date_range: Annotated[str, Query(description="Date range (e.g., '2024-01-01/2024-01-07')")],
    db: Annotated[AsyncSession, Depends(get_db)],
    procedure_code: Annotated[str | None, Query(description="Optional procedure code filter")] = None,
) -> AvailableSlotsResponse:
    """
    Get available appointment slots.

    - **clinic_id**: The clinic UUID
    - **date_range**: Date range in ISO format (start/end)
    - **procedure_code**: Optional filter by procedure code
    """
    # Parse date range
    try:
        start_str, end_str = date_range.split("/")
        start_date = datetime.fromisoformat(start_str)
        end_date = datetime.fromisoformat(end_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range format. Use 'start/end' in ISO format",
        )

    # Validate clinic exists
    clinic_result = await db.execute(
        select(Clinic).where(Clinic.id == clinic_id)
    )
    clinic = clinic_result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clinic {clinic_id} not found",
        )

    # Get active dentists for this clinic
    dentists_result = await db.execute(
        select(Dentist).where(
            Dentist.clinic_id == clinic_id,
            Dentist.is_active == True,
        )
    )
    dentists = dentists_result.scalars().all()

    if not dentists:
        return AvailableSlotsResponse(slots=[])

    # Get existing appointments in the date range
    existing_appointments_result = await db.execute(
        select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    existing_appointments = existing_appointments_result.scalars().all()

    # Get procedure duration if specified
    procedure_duration = 30  # Default
    if procedure_code:
        procedure_result = await db.execute(
            select(Procedure).where(Procedure.code == procedure_code)
        )
        procedure = procedure_result.scalar_one_or_none()
        if procedure:
            procedure_duration = procedure.default_duration_mins

    # Generate available slots
    slots = []
    current_time = start_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9 AM
    end_time = end_date.replace(hour=17, minute=0, second=0, microsecond=0)  # End at 5 PM

    while current_time <= end_time:
        # Skip weekends
        if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            current_time += timedelta(hours=24)
            current_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
            continue

        # Generate slots for each dentist
        for dentist in dentists:
            # Check if this slot conflicts with existing appointments
            slot_available = True
            slot_end = current_time + timedelta(minutes=procedure_duration)

            for appt in existing_appointments:
                if appt.dentist_id == dentist.id:
                    appt_end = appt.start_time + timedelta(minutes=appt.duration_mins)
                    # Check for overlap
                    if not (slot_end <= appt.start_time or current_time >= appt_end):
                        slot_available = False
                        break

            if slot_available:
                slots.append(
                    SlotResponse(
                        id=f"{dentist.id}@{current_time.isoformat()}",
                        start_time=current_time,
                        end_time=slot_end,
                        dentist_id=str(dentist.id),
                        dentist_name=dentist.name,
                    )
                )

        # Move to next time slot (based on procedure duration)
        current_time += timedelta(minutes=procedure_duration)

    return AvailableSlotsResponse(slots=slots)


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new appointment",
    description="Books a new appointment in an available slot.",
)
async def create_appointment(
    request: CreateAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """
    Create a new appointment.

    - **session_id**: The session UUID
    - **patient_id**: The patient UUID
    - **slot_id**: The selected slot UUID
    - **procedure_code**: The dental procedure code
    """
    from uuid import UUID as PyUUID

    # Validate inputs
    try:
        patient_uuid = PyUUID(request.patient_id)
        session_uuid = PyUUID(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format",
        )

    # Get session to find clinic_id
    from src.models import AgentSession

    session_result = await db.execute(
        select(AgentSession).where(AgentSession.session_id == session_uuid)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found",
        )

    clinic_uuid = session.clinic_id

    # Get patient
    patient_result = await db.execute(
        select(Patient).where(Patient.id == patient_uuid)
    )
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {request.patient_id} not found",
        )

    # Parse slot_id to extract dentist_id and start_time
    # Format: "{dentist_id}@{start_time_iso}"
    # Using @ as delimiter to avoid conflicts with UUID and ISO date hyphens
    try:
        dentist_id_str, start_time_str = request.slot_id.split("@", 1)
        dentist_uuid = PyUUID(dentist_id_str)
        start_time = datetime.fromisoformat(start_time_str)
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slot_id format. Expected format: {uuid}@{iso_datetime}",
        )

    # Get dentist and clinic
    dentist_result = await db.execute(
        select(Dentist).where(Dentist.id == dentist_uuid)
    )
    dentist = dentist_result.scalar_one_or_none()

    if not dentist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dentist {dentist_id_str} not found",
        )

    # Get procedure details
    procedure_result = await db.execute(
        select(Procedure).where(Procedure.code == request.procedure_code)
    )
    procedure = procedure_result.scalar_one_or_none()

    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedure {request.procedure_code} not found",
        )

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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected slot is no longer available",
        )

    # Create appointment
    appointment = Appointment(
        id=uuid4(),  # Generate new UUID
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

    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    # Load relationships for response
    appointment_result = await db.execute(
        select(Appointment).options(
            selectinload(Appointment.patient),
            selectinload(Appointment.clinic),
            selectinload(Appointment.dentist),
        ).where(Appointment.id == appointment.id)
    )
    appointment = appointment_result.scalar_one()

    return AppointmentResponse(
        id=str(appointment.id),
        patient_id=str(appointment.patient_id),
        clinic_id=str(appointment.clinic_id),
        dentist_id=str(appointment.dentist_id),
        start_time=appointment.start_time,
        duration_mins=appointment.duration_mins,
        procedure_code=appointment.procedure_code,
        procedure_name=appointment.procedure_name,
        estimated_value=appointment.estimated_value,
        status=appointment.status.value,
    )


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update an appointment",
    description="Updates an existing appointment's status or time.",
)
async def update_appointment(
    appointment_id: UUID,
    request: UpdateAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """
    Update an appointment.

    - **appointment_id**: The appointment UUID
    - **status**: New status (optional)
    - **start_time**: New start time (optional)
    """
    from uuid import UUID as PyUUID

    # Fetch appointment from database
    appointment_result = await db.execute(
        select(Appointment).options(
            selectinload(Appointment.patient),
            selectinload(Appointment.clinic),
            selectinload(Appointment.dentist),
        ).where(Appointment.id == appointment_id)
    )
    appointment = appointment_result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {appointment_id} not found",
        )

    # Update fields if provided
    update_data = {}
    if request.status is not None:
        try:
            appointment.status = AppointmentStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}",
            )

    if request.start_time is not None:
        # Validate new time slot is available
        existing_appointments_result = await db.execute(
            select(Appointment).where(
                Appointment.dentist_id == appointment.dentist_id,
                Appointment.start_time == request.start_time,
                Appointment.id != appointment_id,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        )
        existing_appointments = existing_appointments_result.scalars().all()

        if existing_appointments:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The new time slot is not available",
            )

        appointment.start_time = request.start_time

    # Update timestamp
    appointment.updated_at = datetime.now()

    await db.commit()
    await db.refresh(appointment)

    return AppointmentResponse(
        id=str(appointment.id),
        patient_id=str(appointment.patient_id),
        clinic_id=str(appointment.clinic_id),
        dentist_id=str(appointment.dentist_id),
        start_time=appointment.start_time,
        duration_mins=appointment.duration_mins,
        procedure_code=appointment.procedure_code,
        procedure_name=appointment.procedure_name,
        estimated_value=appointment.estimated_value,
        status=appointment.status.value,
    )


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an appointment",
    description="Cancels an existing appointment.",
)
async def cancel_appointment(
    appointment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Cancel an appointment.

    - **appointment_id**: The appointment UUID
    """
    from uuid import UUID as PyUUID

    # Fetch appointment from database
    appointment_result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = appointment_result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {appointment_id} not found",
        )

    # Set status to CANCELLED
    appointment.status = AppointmentStatus.CANCELLED
    appointment.updated_at = datetime.now()

    await db.commit()

    # Return 204 No Content
