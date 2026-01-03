"""Chat API routes with SSE streaming."""

import asyncio
from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

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
    # TODO: Validate session exists
    # TODO: Queue message for agent processing
    # TODO: Store message in conversation history

    return SendMessageResponse(status="received")


async def generate_sse_events(session_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for the chat stream."""
    # TODO: Connect to actual agent processing
    # This is a placeholder implementation

    # Simulate agent state update
    yield 'event: agent_state\ndata: {"active_agent": "Receptionist", "thinking": true}\n\n'
    await asyncio.sleep(0.5)

    # Simulate token-by-token response
    response_text = "Hello! I'm the PearlFlow dental assistant. How can I help you today?"
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
    # TODO: Validate session exists
    # TODO: Connect to actual agent processing

    return StreamingResponse(
        generate_sse_events(str(session_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
