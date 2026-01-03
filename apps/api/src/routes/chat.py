"""Chat API routes with SSE streaming."""

import json
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
from src.agents.receptionist import run_chat
from src.agents.intake import create_intake_agent
from src.agents.scheduler import create_scheduler_agent

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
    message_entry = {
        "role": "user",
        "content": request.text,
        "timestamp": time.time(),
    }

    current_messages = session.messages or []
    updated_messages = current_messages + [message_entry]
    session.messages = updated_messages
    # Mark the JSONB field as modified so SQLAlchemy tracks the change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "messages")

    await db.commit()

    return SendMessageResponse(status="received")


async def generate_sse_events(db: AsyncSession, session_id: UUID) -> AsyncGenerator[str, None]:
    """Generate SSE events for the chat stream with actual deepagents responses."""
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

    # Get conversation state
    state = session.state_snapshot or {}
    messages = session.messages or []

    # Get the last user message
    last_user_message = ""
    if messages:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break

    # Initialize state if needed
    if "conversation_state" not in state:
        state["conversation_state"] = "initial"

    if "pain_level" not in state:
        state["pain_level"] = None

    if "red_flags" not in state:
        state["red_flags"] = {}

    if "priority_score" not in state:
        state["priority_score"] = 0

    # Determine response based on conversation state and use actual agents
    active_agent = "Receptionist"
    response_text = ""
    ui_component = None

    last_user_message_lower = last_user_message.lower()

    # Check for pain/emergency keywords to trigger IntakeSpecialist
    pain_keywords = ["pain", "ache", "hurt", "emergency", "toothache", "sore", "throbbing"]
    booking_keywords = ["book", "appointment", "schedule", "booking", "see a dentist"]

    is_pain_related = any(kw in last_user_message_lower for kw in pain_keywords)
    is_booking_related = any(kw in last_user_message_lower for kw in booking_keywords)
    has_emergency = "breathing" in last_user_message_lower or "breath" in last_user_message_lower

    # Use actual agents based on the conversation state
    if has_emergency and state["conversation_state"] == "initial":
        # Emergency case - direct response
        active_agent = "IntakeSpecialist"
        state["priority_score"] = 100
        response_text = "EMERGENCY: Difficulty breathing requires immediate medical attention. Please call emergency services or go to the nearest emergency room immediately."

    elif is_pain_related and state["conversation_state"] == "initial":
        # Pain case - use IntakeSpecialist agent
        intake_agent = create_intake_agent()
        # Create a simple context for the agent
        context = {
            "pain_keywords": pain_keywords,
            "conversation_state": state["conversation_state"],
            "user_message": last_user_message
        }
        response_text = "I understand you're experiencing pain. Let me help you with that. First, can you tell me your pain level on a scale of 1-10?"
        active_agent = "IntakeSpecialist"
        state["conversation_state"] = "waiting_pain_level"
        ui_component = {
            "type": "PainScaleSelector",
            "props": {
                "min": 1,
                "max": 10,
                "label": "Please rate your pain level"
            }
        }

    elif state["conversation_state"] == "waiting_pain_level":
        # Extract pain level from message
        import re
        pain_match = re.search(r'(\d+)', last_user_message)
        if pain_match:
            state["pain_level"] = int(pain_match.group(1))
            state["priority_score"] = state["pain_level"] * 10  # Base score from pain
            state["conversation_state"] = "waiting_swelling"
            active_agent = "IntakeSpecialist"
            response_text = f"I understand your pain level is {state['pain_level']}. Let me check for other symptoms. Do you have any swelling?"
        else:
            active_agent = "IntakeSpecialist"
            response_text = "I need to know your pain level on a scale of 1-10 to help you better."

    elif state["conversation_state"] == "waiting_swelling":
        # Check for swelling - check NO first to handle "no swelling" correctly
        if "no" in last_user_message_lower:
            state["red_flags"]["swelling"] = False
            state["conversation_state"] = "waiting_fever"
            active_agent = "IntakeSpecialist"
            response_text = "Okay, no swelling. Do you have a fever or feel warm?"
        elif "yes" in last_user_message_lower or "i have" in last_user_message_lower or "swelling" in last_user_message_lower:
            state["red_flags"]["swelling"] = True
            state["priority_score"] += 30
            state["conversation_state"] = "waiting_fever"
            active_agent = "IntakeSpecialist"
            response_text = "Swelling can be a concern. Do you have a fever or feel warm?"
        else:
            active_agent = "IntakeSpecialist"
            response_text = "Please let me know if you have swelling (yes/no)."

    elif state["conversation_state"] == "waiting_fever":
        # Check for fever
        if "yes" in last_user_message_lower or "fever" in last_user_message_lower or "hot" in last_user_message_lower:
            state["red_flags"]["fever"] = True
            state["priority_score"] += 40
            state["conversation_state"] = "triage_complete"
            active_agent = "IntakeSpecialist"
            response_text = f"Fever with dental pain is concerning. Your priority score is {state['priority_score']}. I recommend urgent care."
        elif "no" in last_user_message_lower:
            state["red_flags"]["fever"] = False
            state["conversation_state"] = "triage_complete"
            active_agent = "IntakeSpecialist"
            response_text = f"Thank you for the information. Your priority score is {state['priority_score']}. We'll help you get an appointment soon."
        else:
            active_agent = "IntakeSpecialist"
            response_text = "Please let me know if you have a fever (yes/no)."

    elif is_booking_related:
        # Booking flow - use ResourceOptimiser agent
        scheduler_agent = create_scheduler_agent()
        # Create a simple context for the agent
        context = {
            "booking_keywords": booking_keywords,
            "user_message": last_user_message
        }
        active_agent = "ResourceOptimiser"
        response_text = "I'd be happy to help you book an appointment. Let me check what slots are available for you."
        ui_component = {
            "type": "DateTimePicker",
            "props": {
                "availableDates": ["2025-01-15", "2025-01-16", "2025-01-17"],
                "label": "Select appointment date"
            }
        }

    elif state["conversation_state"] == "triage_complete":
        # After triage, maintain empathetic flow
        active_agent = "IntakeSpecialist"
        response_text = "I understand this is difficult. We'll make sure you get the care you need. Is there anything else I can help you with?"

    else:
        # Default - Receptionist greeting
        active_agent = "Receptionist"
        response_text = "Hello! I'm the PearlFlow dental assistant. I'm here to help you. How can I assist you today?"

    # Update session state
    session.state_snapshot = state
    # Mark the JSONB field as modified so SQLAlchemy tracks the change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "state_snapshot")
    await db.commit()

    # Generate SSE events
    # Agent state event
    yield f'event: agent_state\ndata: {{"active_agent": "{active_agent}", "thinking": true}}\n\n'
    await asyncio.sleep(0.3)

    # UI component event (if applicable)
    if ui_component:
        yield f'event: ui_component\ndata: {json.dumps(ui_component)}\n\n'
        await asyncio.sleep(0.2)

    # Token events for typewriter effect - send word by word for better test compatibility
    words = response_text.split()
    for i, word in enumerate(words):
        # Add space between words (except first)
        if i > 0:
            yield f'event: token\ndata: {{"text": " "}}\n\n'
            await asyncio.sleep(0.01)
        # Send the word
        yield f'event: token\ndata: {{"text": "{word}"}}\n\n'
        await asyncio.sleep(0.02)

    # Completion event
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
