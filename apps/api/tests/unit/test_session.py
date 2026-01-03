"""Unit tests for session API."""

import pytest
from httpx import AsyncClient
import uuid


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
