"""Heuristics API routes for move scoring and optimization."""

from datetime import date, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Appointment, AppointmentStatus, Patient, Procedure

router = APIRouter()


class MoveScoreRequest(BaseModel):
    """Request model for move score calculation."""

    appointment_id: str
    candidate_slot: str
    new_procedure_value: float


class MoveScoreResponse(BaseModel):
    """Response model for move score calculation."""

    move_score: int
    recommendation: str  # "MOVE" or "KEEP"
    incentive_needed: str


class OptimizeDayRequest(BaseModel):
    """Request model for day optimization."""

    clinic_id: str
    date: date


class MoveSuggestion(BaseModel):
    """A suggested appointment move."""

    source_appointment_id: str
    target_slot: str
    move_score: int
    incentive_needed: str
    potential_revenue_gain: float


class OptimizeDayResponse(BaseModel):
    """Response model for day optimization."""

    suggestions: list[MoveSuggestion]


def calculate_move_score_heuristic(
    current_value: float,
    new_value: float,
    patient_ltv: float,
    days_until_appointment: int,
) -> tuple[int, str, str]:
    """
    Calculate move score based on revenue, LTV, and timing factors.

    Returns:
        Tuple of (move_score, recommendation, incentive)
    """
    # Calculate revenue difference
    revenue_diff = new_value - current_value

    # Base score from revenue difference (0-80 points)
    revenue_score = min(80, max(0, int(revenue_diff / 10)))

    # LTV penalty (high LTV = less likely to move, max 40 points penalty)
    ltv_penalty = min(40, int(patient_ltv / 50))

    # Timing bonus (more notice = higher score, max 20 points)
    timing_bonus = min(20, days_until_appointment * 2)

    # Calculate final score (base 30 points + components)
    move_score = revenue_score - ltv_penalty + timing_bonus + 30
    move_score = max(0, min(100, move_score))

    # Determine incentive and recommendation
    if move_score > 85:
        recommendation = "MOVE"
        incentive = "5% discount"
    elif move_score > 70:
        recommendation = "MOVE"
        incentive = "10% discount"
    elif move_score >= 50:
        recommendation = "CONSIDER"
        incentive = "15% discount or priority slot"
    else:
        recommendation = "KEEP"
        incentive = "No incentive needed"

    return move_score, recommendation, incentive


@router.post(
    "/move-score",
    response_model=MoveScoreResponse,
    summary="Calculate move score",
    description="Calculates the move score for rescheduling an appointment.",
)
async def calculate_move_score(
    request: MoveScoreRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoveScoreResponse:
    """
    Calculate move score for an appointment.

    The move score considers:
    - Revenue difference between current and new appointment
    - Patient LTV (high-value patients are less likely to be moved)
    - Historical acceptance rates
    - Urgency of the new procedure

    - **appointment_id**: The appointment to potentially move
    - **candidate_slot**: The proposed new slot
    - **new_procedure_value**: Revenue value of the new procedure
    """
    # Validate appointment_id
    try:
        appointment_uuid = UUID(request.appointment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid appointment_id format",
        )

    # Fetch appointment
    appointment_result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_uuid)
    )
    appointment = appointment_result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {request.appointment_id} not found",
        )

    # Fetch patient for LTV score
    patient_result = await db.execute(
        select(Patient).where(Patient.id == appointment.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    patient_ltv = patient.ltv_score if patient else 0.0

    # Calculate days until appointment
    days_until = (appointment.start_time - datetime.now()).days
    days_until = max(0, days_until)

    # Calculate move score
    move_score, recommendation, incentive = calculate_move_score_heuristic(
        current_value=appointment.estimated_value,
        new_value=request.new_procedure_value,
        patient_ltv=patient_ltv,
        days_until_appointment=days_until,
    )

    return MoveScoreResponse(
        move_score=move_score,
        recommendation=recommendation,
        incentive_needed=incentive,
    )


@router.post(
    "/optimize-day",
    response_model=OptimizeDayResponse,
    summary="Optimize day schedule",
    description="Analyzes a day's schedule and suggests optimizations.",
)
async def optimize_day(
    request: OptimizeDayRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OptimizeDayResponse:
    """
    Optimize a day's appointment schedule.

    Analyzes all appointments for the given day and suggests
    moves that could improve revenue and chair utilization.

    - **clinic_id**: The clinic UUID
    - **date**: The date to optimize
    """
    # Validate clinic_id
    try:
        clinic_uuid = UUID(request.clinic_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid clinic_id format",
        )

    # Get start and end of day
    day_start = datetime.combine(request.date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    # Fetch all appointments for the day
    appointments_result = await db.execute(
        select(Appointment).where(
            Appointment.clinic_id == clinic_uuid,
            Appointment.start_time >= day_start,
            Appointment.start_time < day_end,
            Appointment.status == AppointmentStatus.BOOKED,
        )
    )
    appointments = appointments_result.scalars().all()

    if not appointments:
        return OptimizeDayResponse(suggestions=[])

    # Get procedure values for comparison
    procedures_result = await db.execute(select(Procedure))
    all_procedures = {p.code: p for p in procedures_result.scalars().all()}

    suggestions = []

    for appt in appointments:
        # Get patient LTV
        patient_result = await db.execute(
            select(Patient).where(Patient.id == appt.patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        patient_ltv = patient.ltv_score if patient else 0.0

        # Find higher-value procedures that could replace this slot
        for proc_code, procedure in all_procedures.items():
            if procedure.base_value > appt.estimated_value * 1.5:  # 50% higher value
                # Calculate move score for this potential replacement
                days_until = (appt.start_time - datetime.now()).days
                days_until = max(0, days_until)

                move_score, recommendation, incentive = calculate_move_score_heuristic(
                    current_value=appt.estimated_value,
                    new_value=procedure.base_value,
                    patient_ltv=patient_ltv,
                    days_until_appointment=days_until,
                )

                if recommendation == "MOVE" and move_score > 70:
                    revenue_gain = procedure.base_value - appt.estimated_value
                    suggestions.append(
                        MoveSuggestion(
                            source_appointment_id=str(appt.id),
                            target_slot=f"{appt.dentist_id}-{appt.start_time.isoformat()}",
                            move_score=move_score,
                            incentive_needed=incentive,
                            potential_revenue_gain=revenue_gain,
                        )
                    )

    # Sort by move_score descending
    suggestions.sort(key=lambda s: s.move_score, reverse=True)

    return OptimizeDayResponse(suggestions=suggestions)
