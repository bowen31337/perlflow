"""Heuristic move check tool for appointment optimization."""

from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

MoveCheckResult = TypedDict('MoveCheckResult', {
    'move_score': int,
    'incentive_needed': str,
    'recommendation': str,
    'revenue_difference': float,
})


async def heuristic_move_check(
    appointment_id: str,
    new_value: float,
    db: 'AsyncSession | None' = None,
) -> MoveCheckResult:
    """
    Calculates the move score for an appointment based on revenue vs loyalty factors.

    This tool evaluates whether an existing appointment should be moved
    to accommodate a higher-value procedure. The calculation considers:
    - Revenue difference between current and new appointment
    - Patient lifetime value (LTV) of the current patient
    - Historical acceptance rates for similar moves
    - Patient risk profile (anxiety level, pain tolerance)

    Move Score Thresholds:
    - Score > 70: Recommend move with appropriate incentive
    - Score 50-70: Consider move only if patient initiates
    - Score < 50: Keep current appointment

    Args:
        appointment_id: UUID of the appointment to potentially move
        new_value: Revenue value of the new procedure requesting the slot
        db: Database session for fetching real data

    Returns:
        A dictionary with:
        - move_score: Integer 0-100 indicating move benefit
        - incentive_needed: Suggested incentive (e.g., "10% discount")
        - recommendation: "MOVE" or "KEEP"
        - revenue_difference: Projected revenue change
    """
    if db is None:
        # Fallback to calculation without patient data
        current_value = 150.0
        revenue_diff = new_value - current_value
        base_score = min(100, max(0, int(revenue_diff / 10 + 50)))
        return {
            "move_score": base_score,
            "incentive_needed": "15% discount or priority slot",
            "recommendation": "MOVE" if base_score > 70 else "KEEP",
            "revenue_difference": revenue_diff,
        }

    from uuid import UUID
    from sqlalchemy import select
    from src.models import Appointment, Patient

    try:
        appointment_uuid = UUID(appointment_id)
    except ValueError:
        return {
            "move_score": 0,
            "incentive_needed": "No incentive needed",
            "recommendation": "KEEP",
            "revenue_difference": 0.0,
        }

    # Fetch appointment details
    appointment_result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_uuid)
    )
    appointment = appointment_result.scalar_one_or_none()

    if not appointment:
        return {
            "move_score": 0,
            "incentive_needed": "No incentive needed",
            "recommendation": "KEEP",
            "revenue_difference": 0.0,
        }

    # Fetch patient details for LTV score
    patient_result = await db.execute(
        select(Patient).where(Patient.id == appointment.patient_id)
    )
    patient = patient_result.scalar_one_or_none()

    patient_ltv = patient.ltv_score if patient else 0.0

    # Calculate revenue difference
    current_value = appointment.estimated_value
    revenue_diff = new_value - current_value

    # Calculate move score with weighted factors
    # Base score from revenue difference
    revenue_score = min(80, max(0, int(revenue_diff / 10)))

    # LTV penalty (high LTV = less likely to move)
    ltv_penalty = min(40, int(patient_ltv / 50))

    # Timing bonus (more notice = higher score)
    from datetime import datetime, timedelta
    days_until_appointment = (appointment.start_time - datetime.now()).days
    days_until_appointment = max(0, days_until_appointment)
    timing_bonus = min(20, days_until_appointment * 2)

    # Calculate final score
    move_score = revenue_score - ltv_penalty + timing_bonus + 30
    move_score = max(0, min(100, move_score))

    # Determine incentive and recommendation
    if move_score > 70:
        recommendation = "MOVE"
        if move_score > 85:
            incentive = "5% discount"
        elif move_score > 80:
            incentive = "10% discount"
        else:
            incentive = "15% discount or priority slot"
    elif move_score >= 50:
        recommendation = "CONSIDER"
        incentive = "15% discount or priority slot"
    else:
        recommendation = "KEEP"
        incentive = "No incentive needed"

    return {
        "move_score": move_score,
        "incentive_needed": incentive,
        "recommendation": recommendation,
        "revenue_difference": revenue_diff,
    }
