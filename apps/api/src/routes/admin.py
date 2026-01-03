"""Admin API routes for analytics and feedback management."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

router = APIRouter()


class AnalyticsResponse(BaseModel):
    """Response model for analytics dashboard."""

    no_show_rate: float
    chair_utilization: float
    revenue_optimization: dict[str, Any]
    move_acceptance_rate: float
    average_triage_accuracy: float


class FeedbackItem(BaseModel):
    """Feedback item for approval."""

    id: str
    patient_id: str
    patient_name: str
    rating: int
    content: str | None
    created_at: str


class PendingFeedbackResponse(BaseModel):
    """Response model for pending feedback."""

    feedback_items: list[FeedbackItem]


class FeedbackResponse(BaseModel):
    """Response model for feedback."""

    id: str
    patient_id: str
    rating: int
    content: str | None
    is_approved: bool
    approved_by: str | None
    approved_at: str | None


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get analytics dashboard",
    description="Retrieves key performance metrics for the dental practice.",
)
async def get_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsResponse:
    """
    Get analytics dashboard data.

    Returns:
    - **no_show_rate**: Percentage of missed appointments
    - **chair_utilization**: Percentage of available time used
    - **revenue_optimization**: Revenue metrics and improvements
    - **move_acceptance_rate**: Rate at which move offers are accepted
    - **average_triage_accuracy**: Accuracy of triage classifications
    """
    # TODO: Calculate metrics from database

    return AnalyticsResponse(
        no_show_rate=5.2,
        chair_utilization=78.5,
        revenue_optimization={
            "current_month": 125000,
            "previous_month": 118000,
            "optimization_gain": 8500,
            "gain_percentage": 7.2,
        },
        move_acceptance_rate=62.3,
        average_triage_accuracy=84.5,
    )


@router.get(
    "/feedback/pending",
    response_model=PendingFeedbackResponse,
    summary="Get pending feedback",
    description="Retrieves feedback items awaiting AHPRA compliance approval.",
)
async def get_pending_feedback(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PendingFeedbackResponse:
    """
    Get feedback items pending approval.

    For AHPRA compliance, all patient feedback must be manually
    reviewed before being displayed publicly.
    """
    # TODO: Query unapproved feedback from database

    return PendingFeedbackResponse(feedback_items=[])


@router.put(
    "/feedback/{feedback_id}/approve",
    response_model=FeedbackResponse,
    summary="Approve feedback",
    description="Approves a feedback item for AHPRA compliance.",
)
async def approve_feedback(
    feedback_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FeedbackResponse:
    """
    Approve a feedback item.

    - **feedback_id**: The feedback UUID to approve
    """
    # TODO: Fetch feedback from database
    # TODO: Set is_approved = True
    # TODO: Set approved_by and approved_at

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Feedback {feedback_id} not found",
    )
