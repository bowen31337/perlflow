"""Session management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import AgentSession, Clinic, SessionStatus
from src.schemas.session import SessionCreate, SessionResponse

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


WELCOME_MESSAGE = (
    "Welcome to PearlFlow! I'm your virtual dental assistant. "
    "How can I help you today? Whether you're experiencing dental issues "
    "or would like to book an appointment, I'm here to assist."
)


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
    # Validate clinic API key
    clinic_result = await db.execute(
        select(Clinic).where(Clinic.api_key == request.clinic_api_key)
    )
    clinic = clinic_result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid clinic API key",
        )

    # Create session in database
    new_session = AgentSession(
        clinic_id=clinic.id,
        status=SessionStatus.ACTIVE,
        current_node="Receptionist",
        messages=[],
        state_snapshot={},
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return CreateSessionResponse(
        session_id=str(new_session.session_id),
        welcome_message=WELCOME_MESSAGE,
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
    # Fetch session from database
    session_result = await db.execute(
        select(AgentSession).where(AgentSession.session_id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return GetSessionResponse(
        session_id=str(session.session_id),
        status=session.status.value,
        current_agent=session.current_node,
    )
