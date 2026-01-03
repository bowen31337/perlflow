"""
Waitlist API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src.services.waitlist_service import waitlist_service
from src.services.waitlist_notifications import waitlist_notification_service

router = APIRouter()


class WaitlistRequest(BaseModel):
    """Request to add patient to waitlist."""
    patient_id: str
    clinic_id: str
    preferred_date_range: Optional[dict] = None
    preferred_time: Optional[str] = None
    procedure_code: Optional[str] = None
    priority_score: int = 0


class WaitlistResponse(BaseModel):
    """Waitlist entry response."""
    success: bool
    waitlist_id: Optional[str] = None
    position: Optional[int] = None


class GetWaitlistResponse(BaseModel):
    """Response for getting waitlist entries."""
    count: int
    waitlist: List[dict]


@router.post("/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist(request: WaitlistRequest):
    """
    POST /waitlist - Add patient to waitlist

    Returns:
        Waitlist entry details
    """
    result = await waitlist_service.add_to_waitlist(
        patient_id=request.patient_id,
        clinic_id=request.clinic_id,
        preferred_date_range=request.preferred_date_range,
        preferred_time=request.preferred_time,
        procedure_code=request.procedure_code,
        priority_score=request.priority_score
    )

    return WaitlistResponse(
        success=True,
        waitlist_id=result["waitlist_id"],
        position=result["position"]
    )


@router.get("/waitlist/{clinic_id}", response_model=GetWaitlistResponse)
async def get_waitlist_by_clinic(clinic_id: str):
    """
    GET /waitlist/{clinic_id} - Get waitlist entries for a clinic

    Returns:
        List of waitlist entries
    """
    entries = await waitlist_service.get_waitlist_by_clinic(clinic_id)
    return GetWaitlistResponse(
        count=len(entries),
        waitlist=entries
    )


@router.post("/waitlist/{waitlist_id}/notify")
async def notify_waitlist_patient(waitlist_id: str):
    """
    POST /waitlist/{waitlist_id}/notify - Notify patient about available slot

    Returns:
        Success status
    """
    success = await waitlist_service.notify_patient(waitlist_id)
    return {"success": success}


@router.put("/waitlist/{waitlist_id}/response")
async def update_waitlist_response(waitlist_id: str, response: str):
    """
    PUT /waitlist/{waitlist_id}/response - Update patient response

    Returns:
        Success status
    """
    success = await waitlist_service.update_response(waitlist_id, response)
    return {"success": success}
