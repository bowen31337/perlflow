"""SMS notification API endpoints."""

from uuid import UUID

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from src.core.database import get_db
from src.schemas.sms import (
    SMSNotificationResponse,
    SMSReminderRequest,
    SMSReminderResponse,
    SMSStatusResponse,
)
from src.services.sms import SMSSenderService

router = APIRouter()


@router.post(
    "/reminders",
    response_model=SMSReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create appointment reminder",
    description="Create an SMS reminder for an appointment",
)
async def create_appointment_reminder(
    request: SMSReminderRequest,
    db=Depends(get_db),
):
    """Create an SMS reminder for an appointment."""
    sms_service = SMSSenderService(db)
    try:
        notification = await sms_service.create_reminder(request)
        return SMSReminderResponse(
            message="SMS reminder scheduled successfully",
            notification_id=str(notification.id),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SMS reminder",
        ) from e


@router.post(
    "/send-pending",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Process pending SMS notifications",
    description="Send all pending SMS notifications that are due",
)
async def process_pending_notifications(
    db=Depends(get_db),
):
    """Process all pending SMS notifications."""
    sms_service = SMSSenderService(db)
    try:
        sent_count = await sms_service.process_pending_notifications()
        return {"message": f"Processed {sent_count} SMS notifications", "sent_count": sent_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process SMS notifications",
        ) from e


@router.get(
    "/notifications/{notification_id}",
    response_model=SMSNotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get SMS notification details",
    description="Get details of a specific SMS notification",
)
async def get_notification_details(
    notification_id: UUID,
    db=Depends(get_db),
):
    """Get details of a specific SMS notification."""
    sms_service = SMSSenderService(db)
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Get notification details not yet implemented",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification details",
        ) from e


@router.put(
    "/notifications/{notification_id}/status",
    response_model=SMSStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Update SMS notification status",
    description="Update the status of an SMS notification",
)
async def update_notification_status(
    notification_id: UUID,
    status_update: dict,
    db=Depends(get_db),
):
    """Update the status of an SMS notification."""
    sms_service = SMSSenderService(db)
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Update notification status not yet implemented",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification status",
        ) from e


@router.get(
    "/stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get SMS notification statistics",
    description="Get statistics about SMS notifications",
)
async def get_sms_stats(
    db=Depends(get_db),
):
    """Get SMS notification statistics."""
    try:
        # This would need to be implemented with actual database queries
        # For now, return a placeholder
        return {
            "total_scheduled": 0,
            "total_sent": 0,
            "total_failed": 0,
            "success_rate": "0%",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SMS statistics",
        ) from e