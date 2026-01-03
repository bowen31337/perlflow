"""Heuristics API routes for move scoring and optimization."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

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
    # TODO: Fetch appointment details
    # TODO: Calculate move score based on heuristics
    # TODO: Determine if move is recommended (score > 70)

    # Placeholder implementation
    return MoveScoreResponse(
        move_score=85,
        recommendation="MOVE",
        incentive_needed="10% discount",
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
    # TODO: Fetch all appointments for the day
    # TODO: Identify low-value appointments
    # TODO: Find potential high-value replacements
    # TODO: Calculate move scores for each suggestion

    return OptimizeDayResponse(suggestions=[])
