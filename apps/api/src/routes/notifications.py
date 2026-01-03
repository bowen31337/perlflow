"""
Notification API routes for SMS and email notifications.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from src.services.sms_service import sms_service


router = APIRouter()


class NotificationRequest(BaseModel):
    """Request model for sending notifications."""
    phone: str = Field(..., description="Phone number in E.164 format")
    type: str = Field(..., description="Notification type: reminder, confirmation, emergency")
    appointment_details: Optional[Dict] = Field(None, description="Appointment information")
    priority: Optional[str] = Field(None, description="Priority level for emergency alerts")
    message: Optional[str] = Field(None, description="Custom message for emergency alerts")


class NotificationResponse(BaseModel):
    """Response model for notification operations."""
    success: bool
    message_id: Optional[str] = None
    status: str = "sent"
    timestamp: str


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks
):
    """
    POST /notifications/send

    Send a notification to a patient.
    """
    try:
        if request.type == "reminder":
            success = await sms_service.send_appointment_reminder(
                phone=request.phone,
                appointment_details=request.appointment_details or {}
            )
        elif request.type == "confirmation":
            success = await sms_service.send_confirmation(
                phone=request.phone,
                appointment_details=request.appointment_details or {}
            )
        elif request.type == "emergency":
            success = await sms_service.send_emergency_alert(
                phone=request.phone,
                priority=request.priority or "URGENT",
                message=request.message or "Emergency alert"
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown notification type: {request.type}")

        if success:
            return NotificationResponse(
                success=True,
                message_id=f"msg_{int(datetime.now().timestamp())}",
                status="sent",
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{message_id}")
async def get_notification_status(message_id: str):
    """
    GET /notifications/status/{message_id}

    Get the status of a notification.
    """
    return {
        "message_id": message_id,
        "status": "delivered",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/history")
async def get_notification_history():
    """
    GET /notifications/history

    Get notification history (for testing/verification).
    """
    return {
        "messages": sms_service.get_sent_messages(),
        "count": len(sms_service.get_sent_messages())
    }
