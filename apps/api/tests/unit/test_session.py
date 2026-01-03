"""Unit tests for session API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    """Test creating a new session."""
    response = await client.post(
        "/session",
        json={"clinic_api_key": "test_key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "welcome_message" in data
    assert len(data["session_id"]) > 0
    assert len(data["welcome_message"]) > 0


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    """Test getting a non-existent session returns 404."""
    response = await client.get("/session/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
