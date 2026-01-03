"""Patients API routes."""

import re
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Patient

router = APIRouter()


# E.164 phone format validation regex
# Format: +[country code][number] e.g., +61412345678
E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")


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

    @field_validator("phone")
    @classmethod
    def validate_e164_format(cls, v: str) -> str:
        """Validate phone number is in E.164 format."""
        if not E164_PATTERN.match(v):
            raise ValueError(
                "Phone must be in E.164 format (e.g., +61412345678). "
                "Must start with + followed by 1-15 digits."
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str | None) -> str | None:
        """Validate email format if provided."""
        if v is None:
            return None
        # Basic email validation
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class UpdatePatientRequest(BaseModel):
    """Request model for updating a patient."""

    risk_profile: dict[str, Any] | None = None
    ltv_score: float | None = None

    @field_validator("ltv_score")
    @classmethod
    def validate_ltv_score(cls, v: float | None) -> float | None:
        """Validate LTV score is non-negative."""
        if v is not None and v < 0:
            raise ValueError("LTV score must be non-negative")
        return v


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
    # Validate E.164 format
    if not E164_PATTERN.match(phone):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Invalid phone format. Must be E.164 format (e.g., +61412345678). "
                "Must start with + followed by 1-15 digits."
            ),
        )

    # Query database for patient
    result = await db.execute(
        select(Patient).where(Patient.phone == phone)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with phone {phone} not found",
        )

    return PatientResponse(
        id=str(patient.id),
        phone=patient.phone,
        name=patient.name,
        email=patient.email,
        risk_profile=patient.risk_profile,
        ltv_score=patient.ltv_score,
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
    # Check for duplicate phone number
    existing_result = await db.execute(
        select(Patient).where(Patient.phone == request.phone)
    )
    existing_patient = existing_result.scalar_one_or_none()

    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with phone {request.phone} already exists",
        )

    # Create new patient
    patient = Patient(
        phone=request.phone,
        name=request.name,
        email=request.email,
        risk_profile={},
        ltv_score=0.0,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    return PatientResponse(
        id=str(patient.id),
        phone=patient.phone,
        name=patient.name,
        email=patient.email,
        risk_profile=patient.risk_profile,
        ltv_score=patient.ltv_score,
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
    # Fetch patient from database
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    # Update fields if provided
    if request.risk_profile is not None:
        patient.risk_profile = request.risk_profile

    if request.ltv_score is not None:
        patient.ltv_score = request.ltv_score

    patient.updated_at = datetime.now()

    await db.commit()
    await db.refresh(patient)

    return PatientResponse(
        id=str(patient.id),
        phone=patient.phone,
        name=patient.name,
        email=patient.email,
        risk_profile=patient.risk_profile,
        ltv_score=patient.ltv_score,
    )
