"""Tests for Patients API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_lookup_patient_by_phone(client: AsyncClient, async_session: AsyncSession):
    """Test looking up a patient by phone number in E.164 format."""
    # First create a patient
    from src.models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        phone="+61412345678",
        name="John Doe",
        email="john@example.com",
        risk_profile={"pain_tolerance": "medium", "anxiety_level": "low"},
        ltv_score=850.0,
    )
    async_session.add(patient)
    await async_session.commit()

    # Lookup patient
    response = await client.get(
        "/patients/lookup",
        params={"phone": "+61412345678"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+61412345678"
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["risk_profile"]["pain_tolerance"] == "medium"
    assert data["ltv_score"] == 850.0


@pytest.mark.asyncio
async def test_lookup_patient_not_found(client: AsyncClient):
    """Test looking up a non-existent patient returns 404."""
    response = await client.get(
        "/patients/lookup",
        params={"phone": "+61999999999"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_lookup_patient_invalid_format(client: AsyncClient):
    """Test looking up a patient with invalid phone format returns 422."""
    response = await client.get(
        "/patients/lookup",
        params={"phone": "0412345678"},  # Missing + prefix
    )

    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower() or "format" in response.json()["detail"].lower()

    response = await client.get(
        "/patients/lookup",
        params={"phone": "+abc12345678"},  # Non-numeric
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_patient_success(client: AsyncClient, async_session: AsyncSession):
    """Test creating a new patient successfully."""
    response = await client.post(
        "/patients",
        json={
            "phone": "+61498765432",
            "name": "Jane Smith",
            "email": "jane@example.com",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "+61498765432"
    assert data["name"] == "Jane Smith"
    assert data["email"] == "jane@example.com"
    assert "id" in data
    assert data["ltv_score"] == 0.0
    assert data["risk_profile"] == {}

    # Verify in database
    from src.models import Patient
    from sqlalchemy import select

    result = await async_session.execute(
        select(Patient).where(Patient.phone == "+61498765432")
    )
    patient = result.scalar_one()
    assert patient.name == "Jane Smith"


@pytest.mark.asyncio
async def test_create_patient_duplicate_phone(client: AsyncClient, async_session: AsyncSession):
    """Test creating a patient with duplicate phone number returns 409."""
    from src.models import Patient
    from uuid import uuid4

    # Create existing patient
    existing = Patient(
        id=uuid4(),
        phone="+61455555555",
        name="Existing Patient",
    )
    async_session.add(existing)
    await async_session.commit()

    # Try to create duplicate
    response = await client.post(
        "/patients",
        json={
            "phone": "+61455555555",
            "name": "New Patient",
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_patient_invalid_phone_format(client: AsyncClient):
    """Test creating a patient with invalid phone format returns 422."""
    # Test with letters - invalid format
    response = await client.post(
        "/patients",
        json={
            "phone": "+61abc456789",  # Contains letters
            "name": "John Doe",
        },
    )

    assert response.status_code == 422

    # Test too short (only 2 digits after country code, minimum is 1)
    response = await client.post(
        "/patients",
        json={
            "phone": "+612",  # Too short (only 1 digit after country code)
            "name": "John Doe",
        },
    )

    assert response.status_code == 422

    # Test starting with 0 after + (invalid country code)
    response = await client.post(
        "/patients",
        json={
            "phone": "+01234567890",  # Country code can't start with 0
            "name": "John Doe",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_patient_invalid_email_format(client: AsyncClient):
    """Test creating a patient with invalid email format returns 422."""
    response = await client.post(
        "/patients",
        json={
            "phone": "+61412345678",
            "name": "John Doe",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_patient_empty_name(client: AsyncClient):
    """Test creating a patient with empty name returns 422."""
    response = await client.post(
        "/patients",
        json={
            "phone": "+61412345678",
            "name": "   ",  # Whitespace only
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_patient_risk_profile(client: AsyncClient, async_session: AsyncSession):
    """Test updating a patient's risk profile."""
    from src.models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        phone="+61411111111",
        name="Test Patient",
    )
    async_session.add(patient)
    await async_session.commit()

    response = await client.put(
        f"/patients/{patient.id}",
        json={
            "risk_profile": {
                "pain_tolerance": "high",
                "anxiety_level": "high",
                "preferred_contact": "email",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["risk_profile"]["pain_tolerance"] == "high"
    assert data["risk_profile"]["anxiety_level"] == "high"

    # Verify in database
    await async_session.refresh(patient)
    assert patient.risk_profile["pain_tolerance"] == "high"


@pytest.mark.asyncio
async def test_update_patient_ltv_score(client: AsyncClient, async_session: AsyncSession):
    """Test updating a patient's LTV score."""
    from src.models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        phone="+61422222222",
        name="Test Patient",
        ltv_score=100.0,
    )
    async_session.add(patient)
    await async_session.commit()

    response = await client.put(
        f"/patients/{patient.id}",
        json={
            "ltv_score": 950.0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ltv_score"] == 950.0

    # Verify in database
    await async_session.refresh(patient)
    assert patient.ltv_score == 950.0


@pytest.mark.asyncio
async def test_update_patient_not_found(client: AsyncClient):
    """Test updating a non-existent patient returns 404."""
    from uuid import uuid4

    response = await client.put(
        f"/patients/{uuid4()}",
        json={
            "ltv_score": 500.0,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_patient_negative_ltv_score(client: AsyncClient, async_session: AsyncSession):
    """Test updating a patient with negative LTV score returns 422."""
    from src.models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        phone="+61433333333",
        name="Test Patient",
    )
    async_session.add(patient)
    await async_session.commit()

    response = await client.put(
        f"/patients/{patient.id}",
        json={
            "ltv_score": -100.0,  # Negative value
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_patient_combined_fields(client: AsyncClient, async_session: AsyncSession):
    """Test updating both risk profile and LTV score together."""
    from src.models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        phone="+61444444444",
        name="Test Patient",
    )
    async_session.add(patient)
    await async_session.commit()

    response = await client.put(
        f"/patients/{patient.id}",
        json={
            "risk_profile": {"pain_tolerance": "low"},
            "ltv_score": 750.0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["risk_profile"]["pain_tolerance"] == "low"
    assert data["ltv_score"] == 750.0

    # Verify in database
    await async_session.refresh(patient)
    assert patient.risk_profile["pain_tolerance"] == "low"
    assert patient.ltv_score == 750.0
