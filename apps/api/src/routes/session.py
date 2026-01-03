"""Session management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.session import SessionCreate, SessionResponse, SessionStatus

router = APIRouter()


class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""

    clinic_api_key: str


class CreateSessionResponse(BaseModel):
    """Response model for session creation."""

    session_id: str
    welcome_message: str


class GetSessionResponse(BaseModel):
    """Response model for getting session details."""

    session_id: str
    status: str
    current_agent: str


@router.post(
    "",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a new chat session",
    description="Creates a new chat session for the widget using the clinic API key.",
)
async def create_session(
    request: CreateSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CreateSessionResponse:
    """
    Create a new chat session.

    - **clinic_api_key**: The clinic's API key for authentication
    """
    # TODO: Validate clinic API key
    # TODO: Create session in database
    # TODO: Initialize agent state

    # Placeholder implementation
    import uuid

    session_id = str(uuid.uuid4())
    welcome_message = (
        "Welcome to PearlFlow! I'm your virtual dental assistant. "
        "How can I help you today? Whether you're experiencing dental issues "
        "or would like to book an appointment, I'm here to assist."
    )

    return CreateSessionResponse(
        session_id=session_id,
        welcome_message=welcome_message,
    )


@router.get(
    "/{session_id}",
    response_model=GetSessionResponse,
    summary="Get session details",
    description="Retrieves the current status and details of an existing session.",
)
async def get_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GetSessionResponse:
    """
    Get session details by ID.

    - **session_id**: The session UUID
    """
    # TODO: Fetch session from database
    # TODO: Return session details

    # Placeholder implementation - in production, fetch from DB
    # For now, raise 404 for any request
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Session {session_id} not found",
    )
