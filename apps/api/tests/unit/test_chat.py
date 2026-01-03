"""Unit tests for chat API."""

import pytest
from httpx import AsyncClient
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import AgentSession


def extract_text_from_sse(sse_data: str) -> str:
    """Extract and combine text content from SSE token events.

    Args:
        sse_data: Raw SSE event stream data

    Returns:
        Combined text content from all token events
    """
    tokens = []
    for line in sse_data.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'text' in data:
                    tokens.append(data['text'])
            except (json.JSONDecodeError, KeyError):
                pass
    return ''.join(tokens)


@pytest.mark.asyncio
async def test_send_message_valid_session(client: AsyncClient, test_clinic):
    """Test sending a message to a valid session returns acknowledgment."""
    # First create a session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send a message
    response = await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have a toothache"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


@pytest.mark.asyncio
async def test_send_message_invalid_session(client: AsyncClient):
    """Test sending a message to an invalid session returns 404."""
    random_uuid = str(uuid.uuid4())
    response = await client.post(
        "/chat/message",
        json={"session_id": random_uuid, "text": "Hello"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_chat_valid_session(client: AsyncClient, test_clinic):
    """Test SSE streaming returns token events."""
    # First create a session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send a message first
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "Hello"},
    )

    # Then stream
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        assert response.status_code == 200
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk

        # Should contain at least agent_state and token events
        assert "agent_state" in combined
        assert "token" in combined
        assert "complete" in combined


@pytest.mark.asyncio
async def test_stream_chat_invalid_session(client: AsyncClient):
    """Test SSE streaming with invalid session returns error event."""
    random_uuid = str(uuid.uuid4())

    async with client.stream("GET", f"/chat/stream/{random_uuid}") as response:
        assert response.status_code == 200
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk or "error" in chunk:
                break

        # Should contain error event
        assert "error" in combined.lower()


@pytest.mark.asyncio
async def test_stream_chat_pain_context(client: AsyncClient, test_clinic):
    """Test SSE streaming responds appropriately to pain-related messages."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache"},
    )

    # Stream and check response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

        # Should use IntakeSpecialist agent
        assert "intakespecialist" in combined.lower()


@pytest.mark.asyncio
async def test_stream_chat_booking_context(client: AsyncClient, test_clinic):
    """Test SSE streaming responds appropriately to booking-related messages."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send booking message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I want to book an appointment"},
    )

    # Stream and check response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

        # Should use ResourceOptimiser agent
        assert "resourceoptimiser" in combined.lower()


@pytest.mark.asyncio
async def test_send_message_stores_in_history(client: AsyncClient, test_clinic, async_session):
    """Test that sent messages are stored in session history."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "Test message"},
    )

    # Verify message is in database using a fresh query
    result = await async_session.execute(
        select(AgentSession).where(AgentSession.session_id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    assert session is not None
    assert session.messages is not None
    assert len(session.messages) == 1
    assert session.messages[0]["role"] == "user"
    assert session.messages[0]["content"] == "Test message"


@pytest.mark.asyncio
async def test_receptionist_polite_tone(client: AsyncClient, test_clinic):
    """Test that Receptionist maintains polite and helpful tone."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send greeting message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "Hello"},
    )

    # Stream and check response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

    # Verify polite and welcoming tone
    assert "welcome" in combined.lower() or "hello" in combined.lower()
    assert "help" in combined.lower()
    # Verify no technical jargon
    assert "json" not in combined.lower()
    assert "api" not in combined.lower()


@pytest.mark.asyncio
async def test_intake_specialist_pain_level(client: AsyncClient, test_clinic):
    """Test that IntakeSpecialist asks for pain level on 1-10 scale."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache"},
    )

    # Stream and check response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

    # Verify asks for pain level
    assert "pain" in combined.lower()
    assert "1" in combined or "10" in combined or "scale" in combined.lower()


@pytest.mark.asyncio
async def test_intake_specialist_swelling_check(client: AsyncClient, test_clinic):
    """Test that IntakeSpecialist checks for swelling red flag."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache"},
    )

    # Stream first response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined1 = ""
        async for chunk in response.aiter_text():
            combined1 += chunk
            if "complete" in chunk:
                break

    # Verify IntakeSpecialist is active
    assert "intakespecialist" in combined1.lower()

    # Send pain level response
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "My pain level is 8"},
    )

    # Stream second response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined2 = ""
        async for chunk in response.aiter_text():
            combined2 += chunk
            if "complete" in chunk:
                break

    # Verify asks about swelling
    assert "swelling" in combined2.lower()


@pytest.mark.asyncio
async def test_intake_specialist_fever_check(client: AsyncClient, test_clinic):
    """Test that IntakeSpecialist checks for fever red flag."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache"},
    )

    # Stream first response and send pain level
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "My pain level is 8"},
    )

    # Stream second response and send swelling response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "No swelling"},
    )

    # Stream third response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

    # Verify asks about fever
    assert "fever" in combined.lower()


@pytest.mark.asyncio
async def test_intake_specialist_priority_score(client: AsyncClient, test_clinic):
    """Test that IntakeSpecialist outputs PRIORITY score after triage."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache"},
    )

    # Stream and send responses through triage flow
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "My pain level is 9"},
    )

    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "Yes, I have swelling"},
    )

    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "No fever"},
    )

    # Stream final response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

    # Extract text from SSE events for proper phrase matching
    text_content = extract_text_from_sse(combined).lower()

    # Verify priority score is mentioned
    assert "priority" in text_content or "urgent" in text_content


@pytest.mark.asyncio
async def test_intake_specialist_empathetic_flow(client: AsyncClient, test_clinic):
    """Test that IntakeSpecialist maintains empathetic conversational flow."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send distressing pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I'm in terrible pain, please help me"},
    )

    # Stream response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

    # Extract text from SSE events for proper phrase matching
    text_content = extract_text_from_sse(combined).lower()

    # Verify empathetic language
    assert "understand" in text_content or "help" in text_content
    # Verify supportive (not clinical/dismissive) language
    assert "sorry" in text_content or "i understand" in text_content


@pytest.mark.asyncio
async def test_intake_specialist_emergency_breathing_difficulty(client: AsyncClient, test_clinic):
    """Test that IntakeSpecialist recognizes breathing difficulty as emergency."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache and difficulty breathing"},
    )

    # Stream response
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        combined = ""
        async for chunk in response.aiter_text():
            combined += chunk
            if "complete" in chunk:
                break

    # Extract text from SSE events for proper phrase matching
    text_content = extract_text_from_sse(combined).lower()

    # Verify emergency recognition
    assert "emergency" in text_content or "immediate" in text_content or "urgent" in text_content
