"""Unit tests for session API."""

import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AgentSession, SessionStatus


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, test_clinic):
    """Test creating a new session with valid clinic API key."""
    response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "welcome_message" in data
    assert len(data["session_id"]) > 0
    assert len(data["welcome_message"]) > 0
    # Verify session_id is a valid UUID
    uuid.UUID(data["session_id"])


@pytest.mark.asyncio
async def test_create_session_invalid_api_key(client: AsyncClient):
    """Test creating a session with invalid API key returns 401."""
    response = await client.post(
        "/session",
        json={"clinic_api_key": "invalid_key"},
    )

    assert response.status_code == 401
    assert "Invalid clinic API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_session_found(client: AsyncClient, test_clinic, async_session):
    """Test getting an existing session returns session details."""
    # First create a session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Then get the session
    response = await client.get(f"/session/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["status"] == "ACTIVE"
    assert data["current_agent"] == "Receptionist"


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    """Test getting a non-existent session returns 404."""
    random_uuid = str(uuid.uuid4())
    response = await client.get(f"/session/{random_uuid}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_session_persistence_checkpoint_stored(client: AsyncClient, test_clinic, async_session):
    """Test that session state is stored in PostgreSQL after interaction."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send a message to trigger state update
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have a toothache"},
    )

    # Stream the response to complete the interaction
    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    # Query the database directly
    result = await async_session.execute(
        select(AgentSession).where(AgentSession.session_id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()

    assert session is not None
    assert session.state_snapshot is not None
    assert "conversation_state" in session.state_snapshot
    assert session.current_node == "IntakeSpecialist"
    assert len(session.messages) > 0


@pytest.mark.asyncio
async def test_session_persistence_state_recovered(client: AsyncClient, test_clinic, async_session):
    """Test that session state is recovered after reconnection."""
    # Create session and have conversation
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Send pain message and get response
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have severe toothache"},
    )

    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    # Get session details (simulating reconnection)
    response = await client.get(f"/session/{session_id}")
    assert response.status_code == 200
    data = response.json()

    # Verify state is preserved
    assert data["status"] == "ACTIVE"
    assert data["current_agent"] == "IntakeSpecialist"


@pytest.mark.asyncio
async def test_concurrent_sessions_per_clinic(client: AsyncClient, test_clinic, async_session):
    """Test that multiple concurrent sessions are supported per clinic."""
    # Create multiple sessions for the same clinic
    session_ids = []
    for _ in range(3):
        response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session_ids.append(response.json()["session_id"])

    # Verify all sessions are unique
    assert len(set(session_ids)) == 3

    # Interact with each session independently
    for session_id in session_ids:
        await client.post(
            "/chat/message",
            json={"session_id": session_id, "text": "Hello"},
        )

        async with client.stream("GET", f"/chat/stream/{session_id}") as response:
            combined = ""
            async for chunk in response.aiter_text():
                combined += chunk
                if "complete" in chunk:
                    break

        # Verify each session responds
        assert len(combined) > 0


@pytest.mark.asyncio
async def test_session_status_transitions(client: AsyncClient, test_clinic, async_session):
    """Test that session status transitions correctly."""
    # Create session
    create_response = await client.post(
        "/session",
        json={"clinic_api_key": test_clinic.api_key},
    )
    session_id = create_response.json()["session_id"]

    # Verify initial status is ACTIVE
    result = await async_session.execute(
        select(AgentSession).where(AgentSession.session_id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    assert session.status == SessionStatus.ACTIVE

    # Send messages and verify status remains ACTIVE during conversation
    await client.post(
        "/chat/message",
        json={"session_id": session_id, "text": "I have a toothache"},
    )

    async with client.stream("GET", f"/chat/stream/{session_id}") as response:
        async for chunk in response.aiter_text():
            if "complete" in chunk:
                break

    # Refresh session
    await async_session.refresh(session)
    assert session.status == SessionStatus.ACTIVE
