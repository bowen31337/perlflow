"""
Waitlist API endpoints.
Future enhancement - handles waitlist operations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class WaitlistRequest(BaseModel):
    """Request to add patient to waitlist."""
    patient_id: str
    procedure_code: str
    preferred_date: str


class WaitlistResponse(BaseModel):
    """Waitlist entry response."""
    waitlist_id: str
    patient_id: str
    procedure_code: str
    preferred_date: str
    status: str


@router.post("/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist(request: WaitlistRequest):
    """
    POST /waitlist - Add patient to waitlist
    
    Args:
        request: Waitlist request details
        
    Returns:
        Waitlist entry
    """
    # Placeholder for waitlist addition
    return WaitlistResponse(
        waitlist_id="test-id",
        patient_id=request.patient_id,
        procedure_code=request.procedure_code,
        preferred_date=request.preferred_date,
        status="active"
    )


@router.get("/waitlist", response_model=List[WaitlistResponse])
async def get_waitlist(procedure_code: Optional[str] = None):
    """
    GET /waitlist - Get waitlist entries
    
    Args:
        procedure_code: Optional filter
        
    Returns:
        List of waitlist entries
    """
    # Placeholder for waitlist retrieval
    return []


@router.delete("/waitlist/{waitlist_id}")
async def remove_from_waitlist(waitlist_id: str):
    """
    DELETE /waitlist/{waitlist_id} - Remove from waitlist
    
    Args:
        waitlist_id: Waitlist entry ID
        
    Returns:
        Success status
    """
    # Placeholder for waitlist removal
    return {"status": "removed"}
