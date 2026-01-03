"""Move offer tool for patient rescheduling incentives."""

from typing import TypedDict


class OfferResult(TypedDict):
    """Result of sending a move offer."""

    offer_id: str
    status: str
    original_appointment_id: str
    proposed_new_slot: str
    incentive: str
    expiry: str
    notification_sent: bool


async def send_move_offer(
    original_appointment_id: str,
    new_slot: str,
    incentive: str,
) -> dict:
    """
    Initiates an outbound offer to a patient for voluntary rescheduling.

    This tool creates a move offer record and sends a notification
    to the patient, offering an incentive to reschedule their
    appointment to free up their original slot for a higher-value
    procedure.

    The offer process:
    1. Creates a move_offer record with PENDING status
    2. Generates the incentive offer message
    3. Sends notification via patient's preferred channel
    4. Sets expiry time for the offer
    5. Returns tracking information

    AHPRA Compliance:
    - All messaging must be factual and non-coercive
    - Patient must have clear option to decline
    - No pressure tactics or false urgency

    Args:
        original_appointment_id: UUID of the appointment to move
        new_slot: Proposed new slot ID for the rescheduled appointment
        incentive: The incentive offer (e.g., "10% discount", "priority slot")

    Returns:
        A dictionary with offer tracking:
        - offer_id: UUID of the created offer
        - status: "PENDING"
        - original_appointment_id: The appointment being offered to move
        - proposed_new_slot: The suggested alternative time
        - incentive: The incentive being offered
        - expiry: When the offer expires
        - notification_sent: Whether notification was successfully sent
    """
    # TODO: Implement actual offer logic
    # This would:
    # 1. Fetch original appointment details
    # 2. Validate new slot is available
    # 3. Create move_offer record
    # 4. Send notification to patient
    # 5. Return offer details

    import uuid
    from datetime import datetime, timedelta

    # Placeholder implementation
    expiry = datetime.now() + timedelta(hours=24)

    return {
        "offer_id": str(uuid.uuid4()),
        "status": "PENDING",
        "original_appointment_id": original_appointment_id,
        "proposed_new_slot": new_slot,
        "incentive": incentive,
        "expiry": expiry.isoformat(),
        "notification_sent": True,
    }
