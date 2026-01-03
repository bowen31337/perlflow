"""Patients API routes."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

router = APIRouter()


class PatientResponse(BaseModel):
    """Response model for patient data."""

    id: str
    phone: str
    name: str
    email: str | None
    risk_profile: dict[str, Any] | None
    ltv_score: float


class CreatePatientRequest(BaseModel):
    """Request model for creating a patient."""

    phone: str
    name: str
    email: str | None = None


class UpdatePatientRequest(BaseModel):
    """Request model for updating a patient."""

    risk_profile: dict[str, Any] | None = None
    ltv_score: float | None = None


@router.get(
    "/lookup",
    response_model=PatientResponse,
    summary="Lookup patient by phone",
    description="Finds a patient by their phone number (E.164 format).",
)
async def lookup_patient(
    phone: Annotated[str, Query(description="Phone number in E.164 format (e.g., +61412345678)")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """
    Lookup patient by phone number.

    - **phone**: Phone number in E.164 format
    """
    # TODO: Validate E.164 format
    # TODO: Query database for patient

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Patient with phone {phone} not found",
    )


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new patient",
    description="Creates a new patient record.",
)
async def create_patient(
    request: CreatePatientRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """
    Create a new patient.

    - **phone**: Phone number in E.164 format
    - **name**: Patient's full name
    - **email**: Optional email address
    """
    # TODO: Validate E.164 phone format
    # TODO: Check for duplicate phone
    # TODO: Create patient in database

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Patient creation not yet implemented",
    )


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update patient information",
    description="Updates a patient's risk profile or LTV score.",
)
async def update_patient(
    patient_id: UUID,
    request: UpdatePatientRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """
    Update patient information.

    - **patient_id**: The patient UUID
    - **risk_profile**: Optional risk profile with pain_tolerance, anxiety_level
    - **ltv_score**: Optional lifetime value score
    """
    # TODO: Fetch patient from database
    # TODO: Update fields
    # TODO: Save changes

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Patient {patient_id} not found",
    )
