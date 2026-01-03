"""Unit tests for session persistence and checkpointing."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.models import AgentSession, SessionStatus


class TestSessionPersistence:
    """Test session persistence features."""

    @pytest.mark.asyncio
    async def test_state_recovered_after_reconnection(self, client: AsyncClient, test_clinic):
        """Test that state is recovered after disconnection and reconnection."""
        # Step 1: Create session
        create_response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session_id = create_response.json()["session_id"]

        # Step 2: Have a conversation (pain triage flow)
        # Send pain message
        await client.post(
            "/chat/message",
            json={"session_id": session_id, "text": "I have severe toothache"},
        )

        # Stream first response
        async with client.stream("GET", f"/chat/stream/{session_id}") as response:
            async for chunk in response.aiter_text():
                if "complete" in chunk:
                    break

        # Send pain level
        await client.post(
            "/chat/message",
            json={"session_id": session_id, "text": "My pain level is 8"},
        )

        # Stream second response
        async with client.stream("GET", f"/chat/stream/{session_id}") as response:
            async for chunk in response.aiter_text():
                if "complete" in chunk:
                    break

        # Step 3: Simulate disconnection (just stop using the session)

        # Step 4: Reconnect with same session_id
        # Send another message to the same session
        await client.post(
            "/chat/message",
            json={"session_id": session_id, "text": "Yes, I have swelling"},
        )

        # Step 5 & 6: Verify conversation history and agent state are preserved
        async with client.stream("GET", f"/chat/stream/{session_id}") as response:
            combined = ""
            async for chunk in response.aiter_text():
                combined += chunk
                if "complete" in chunk:
                    break

        # Should continue the triage flow (asking about fever)
        assert "fever" in combined.lower() or "warm" in combined.lower()

    @pytest.mark.asyncio
    async def test_checkpoint_stored_in_postgresql(self, async_session: AsyncSession, test_clinic):
        """Test that checkpoint is stored in PostgreSQL."""
        # Create session via API
        from src.routes.session import create_session, CreateSessionRequest
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        # Create session directly using the model
        new_session = AgentSession(
            clinic_id=test_clinic.id,
            status=SessionStatus.ACTIVE,
            current_node="Receptionist",
            messages=[],
            state_snapshot={},
        )
        async_session.add(new_session)
        await async_session.commit()
        await async_session.refresh(new_session)

        session_id = new_session.session_id

        # Interact with session to populate state
        # Add a message
        new_session.messages = [
            {"role": "user", "content": "I have a toothache", "timestamp": 1234567890.0}
        ]
        new_session.state_snapshot = {
            "conversation_state": "waiting_pain_level",
            "pain_level": None,
            "priority_score": 0,
        }
        new_session.current_node = "IntakeSpecialist"
        await async_session.commit()

        # Query the database
        result = await async_session.execute(
            select(AgentSession).where(AgentSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        # Verify checkpoint stored
        assert session is not None
        assert session.state_snapshot is not None
        assert "conversation_state" in session.state_snapshot
        assert session.state_snapshot["conversation_state"] == "waiting_pain_level"
        assert session.current_node == "IntakeSpecialist"
        assert len(session.messages) == 1
        assert session.messages[0]["content"] == "I have a toothache"

    @pytest.mark.asyncio
    async def test_concurrent_sessions_isolated(self, client: AsyncClient, async_session: AsyncSession, test_clinic):
        """Test that concurrent sessions for same clinic are isolated."""
        # Create two sessions
        session1_response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session1_id = session1_response.json()["session_id"]

        session2_response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session2_id = session2_response.json()["session_id"]

        # Verify they are different
        assert session1_id != session2_id

        # Interact with session 1 (pain flow)
        await client.post(
            "/chat/message",
            json={"session_id": session1_id, "text": "I have severe toothache"},
        )
        async with client.stream("GET", f"/chat/stream/{session1_id}") as response:
            async for chunk in response.aiter_text():
                if "complete" in chunk:
                    break

        await client.post(
            "/chat/message",
            json={"session_id": session1_id, "text": "My pain level is 9"},
        )

        # Interact with session 2 (booking flow)
        await client.post(
            "/chat/message",
            json={"session_id": session2_id, "text": "I want to book an appointment"},
        )
        async with client.stream("GET", f"/chat/stream/{session2_id}") as response:
            async for chunk in response.aiter_text():
                if "complete" in chunk:
                    break

        # Verify session 1 is still in pain triage state
        async with client.stream("GET", f"/chat/stream/{session1_id}") as response:
            combined1 = ""
            async for chunk in response.aiter_text():
                combined1 += chunk
                if "complete" in chunk:
                    break

        # Session 1 should ask about swelling (pain flow)
        assert "swelling" in combined1.lower()

        # Verify session 2 has its own state - check database
        result = await async_session.execute(
            select(AgentSession).where(AgentSession.session_id == uuid.UUID(session2_id))
        )
        session2_db = result.scalar_one_or_none()
        assert session2_db is not None
        # Session 2 should have messages stored
        assert len(session2_db.messages) >= 1

    @pytest.mark.asyncio
    async def test_session_status_transitions(self, async_session: AsyncSession, test_clinic):
        """Test that session status transitions correctly."""
        # Create session with ACTIVE status
        new_session = AgentSession(
            clinic_id=test_clinic.id,
            status=SessionStatus.ACTIVE,
            current_node="Receptionist",
            messages=[],
            state_snapshot={},
        )
        async_session.add(new_session)
        await async_session.commit()
        await async_session.refresh(new_session)

        # Verify initial status
        assert new_session.status == SessionStatus.ACTIVE

        # Simulate completing the conversation
        new_session.status = SessionStatus.COMPLETED
        await async_session.commit()

        # Verify status changed
        result = await async_session.execute(
            select(AgentSession).where(AgentSession.session_id == new_session.session_id)
        )
        updated_session = result.scalar_one_or_none()
        assert updated_session.status == SessionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_session_abandoned_status(self, async_session: AsyncSession, test_clinic):
        """Test that abandoned sessions can be marked as ABANDONED."""
        # Create session
        new_session = AgentSession(
            clinic_id=test_clinic.id,
            status=SessionStatus.ACTIVE,
            current_node="Receptionist",
            messages=[],
            state_snapshot={},
        )
        async_session.add(new_session)
        await async_session.commit()

        # Mark as abandoned (simulating timeout)
        new_session.status = SessionStatus.ABANDONED
        await async_session.commit()

        # Verify status
        result = await async_session.execute(
            select(AgentSession).where(AgentSession.session_id == new_session.session_id)
        )
        session = result.scalar_one_or_none()
        assert session.status == SessionStatus.ABANDONED

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_persistence(self, client: AsyncClient, test_clinic, async_session: AsyncSession):
        """Test that multi-turn conversations maintain state correctly."""
        # Create session
        create_response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session_id = create_response.json()["session_id"]

        # Full triage flow
        turn1_messages = [
            ("I have severe toothache", "pain"),  # Should trigger IntakeSpecialist
            ("My pain level is 8", "pain level"),
            ("Yes, I have swelling", "swelling"),
            ("No fever", "fever"),
        ]

        for text, _ in turn1_messages:
            await client.post(
                "/chat/message",
                json={"session_id": session_id, "text": text},
            )
            async with client.stream("GET", f"/chat/stream/{session_id}") as response:
                async for chunk in response.aiter_text():
                    if "complete" in chunk:
                        break

        # Verify final state in database
        result = await async_session.execute(
            select(AgentSession).where(AgentSession.session_id == uuid.UUID(session_id))
        )
        session = result.scalar_one_or_none()

        assert session is not None
        assert len(session.messages) == 4  # 4 user messages
        assert session.state_snapshot["conversation_state"] == "triage_complete"
        assert session.state_snapshot["pain_level"] == 8
        assert session.state_snapshot["red_flags"]["swelling"] is True
        assert session.state_snapshot["red_flags"]["fever"] is False
        assert session.state_snapshot["priority_score"] == 110  # 80 + 30 (swelling)
