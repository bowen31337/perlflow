"""Heuristic move check tool for appointment optimization."""

from typing import TypedDict


class MoveCheckResult(TypedDict):
    """Result of a move check calculation."""

    move_score: int
    incentive_needed: str
    recommendation: str
    revenue_difference: float


async def heuristic_move_check(appointment_id: str, new_value: float) -> dict:
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

    Returns:
        A dictionary with:
        - move_score: Integer 0-100 indicating move benefit
        - incentive_needed: Suggested incentive (e.g., "10% discount")
        - recommendation: "MOVE" or "KEEP"
        - revenue_difference: Projected revenue change
    """
    # TODO: Implement actual heuristic calculation
    # This would:
    # 1. Fetch the appointment from database
    # 2. Get the procedure value of current appointment
    # 3. Get patient LTV score
    # 4. Calculate move score based on weighted factors
    # 5. Determine appropriate incentive

    # Placeholder implementation with realistic logic
    current_value = 150.0  # Placeholder - would fetch from DB

    revenue_diff = new_value - current_value

    # Simple scoring algorithm (placeholder)
    base_score = min(100, max(0, int(revenue_diff / 10 + 50)))

    # Adjust for patient LTV (placeholder - high LTV reduces score)
    patient_ltv = 500.0  # Placeholder
    ltv_adjustment = -int(patient_ltv / 100)
    move_score = max(0, min(100, base_score + ltv_adjustment))

    # Determine incentive based on score
    if move_score >= 80:
        incentive = "5% discount"
    elif move_score >= 70:
        incentive = "10% discount"
    else:
        incentive = "15% discount or priority slot"

    recommendation = "MOVE" if move_score > 70 else "KEEP"

    return {
        "move_score": move_score,
        "incentive_needed": incentive,
        "recommendation": recommendation,
        "revenue_difference": revenue_diff,
    }
