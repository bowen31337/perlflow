"""Appointments API routes."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

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
    procedure_code: str


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
    procedure_code: Annotated[str | None, Query(description="Optional procedure code filter")] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AvailableSlotsResponse:
    """
    Get available appointment slots.

    - **clinic_id**: The clinic UUID
    - **date_range**: Date range in ISO format (start/end)
    - **procedure_code**: Optional filter by procedure code
    """
    # TODO: Query database for available slots
    # TODO: Filter by procedure duration requirements
    # TODO: Respect operating hours and dentist schedules

    return AvailableSlotsResponse(slots=[])


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
    # TODO: Validate slot is still available
    # TODO: Create appointment in database
    # TODO: Return appointment details

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Appointment creation not yet implemented",
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
    # TODO: Fetch appointment from database
    # TODO: Update fields
    # TODO: Validate new time slot if changing time

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Appointment {appointment_id} not found",
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
    # TODO: Fetch appointment from database
    # TODO: Set status to CANCELLED
    # TODO: Free up the slot

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Appointment {appointment_id} not found",
    )
