"""Chat API routes with SSE streaming."""

import asyncio
from typing import Annotated, AsyncGenerator
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import AgentSession, SessionStatus

router = APIRouter()


class SendMessageRequest(BaseModel):
    """Request model for sending a chat message."""

    session_id: str
    text: str


class SendMessageResponse(BaseModel):
    """Response model for message acknowledgment."""

    status: str


@router.post(
    "/message",
    response_model=SendMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description="Sends a message to the agent for processing. Connect to SSE stream for response.",
)
async def send_message(
    request: SendMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SendMessageResponse:
    """
    Send a chat message to the agent.

    - **session_id**: The session UUID
    - **text**: The message text content
    """
    # Validate session exists
    try:
        session_uuid = UUID(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format",
        )

    session_result = await db.execute(
        select(AgentSession).where(
            AgentSession.session_id == session_uuid,
            AgentSession.status == SessionStatus.ACTIVE,
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found or not active",
        )

    # Store message in conversation history
    # IMPORTANT: Create new list to ensure SQLAlchemy detects the change
    message_entry = {
        "role": "user",
        "content": request.text,
        "timestamp": time.time(),
    }

    current_messages = session.messages or []
    updated_messages = current_messages + [message_entry]
    session.messages = updated_messages

    await db.commit()

    return SendMessageResponse(status="received")


async def generate_sse_events(db: AsyncSession, session_id: UUID) -> AsyncGenerator[str, None]:
    """Generate SSE events for the chat stream with context-aware responses."""
    # Validate session exists
    session_result = await db.execute(
        select(AgentSession).where(
            AgentSession.session_id == session_id,
            AgentSession.status == SessionStatus.ACTIVE,
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        yield 'event: error\ndata: {"error": "Session not found"}\n\n'
        return

    # Get the last user message for context
    user_message = ""
    if session.messages:
        for msg in reversed(session.messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

    # Determine agent context based on user message
    user_message_lower = user_message.lower()
    if any(keyword in user_message_lower for keyword in ["pain", "ache", "hurt", "emergency", "toothache"]):
        # Pain/emergency context - IntakeSpecialist
        active_agent = "IntakeSpecialist"
        response_text = "I understand you're experiencing pain. Let me help you with that. First, can you tell me your pain level on a scale of 1-10?"
    elif any(keyword in user_message_lower for keyword in ["book", "appointment", "schedule", "booking"]):
        # Booking context - ResourceOptimiser
        active_agent = "ResourceOptimiser"
        response_text = "I'd be happy to help you book an appointment. Let me check what slots are available for you."
    else:
        # Default context - Receptionist
        active_agent = "Receptionist"
        response_text = "Hello! I'm the PearlFlow dental assistant. How can I help you today?"

    # Simulate agent state update
    yield f'event: agent_state\ndata: {{"active_agent": "{active_agent}", "thinking": true}}\n\n'
    await asyncio.sleep(0.3)

    # Simulate token-by-token response
    for char in response_text:
        yield f'event: token\ndata: {{"text": "{char}"}}\n\n'
        await asyncio.sleep(0.02)

    # Signal completion
    yield 'event: complete\ndata: {"status": "done"}\n\n'


@router.get(
    "/stream/{session_id}",
    summary="Stream chat responses",
    description="SSE endpoint for receiving real-time chat responses with typewriter effect.",
    responses={
        200: {
            "description": "SSE stream of chat events",
            "content": {
                "text/event-stream": {
                    "example": 'event: token\ndata: {"text": "H"}\n\n'
                }
            },
        }
    },
)
async def stream_chat(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """
    Stream chat responses via Server-Sent Events.

    Events:
    - **token**: Partial text for typewriter effect
    - **agent_state**: Agent status updates (active_agent, thinking)
    - **ui_component**: Generative UI component to render
    - **complete**: Final message signal

    - **session_id**: The session UUID
    """
    return StreamingResponse(
        generate_sse_events(db, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
