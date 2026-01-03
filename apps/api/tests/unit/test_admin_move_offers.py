"""Tests for admin move offer endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from src.models import MoveOffer, MoveOfferStatus, IncentiveType, Clinic, Dentist


@pytest.mark.asyncio
async def test_expire_old_offers_endpoint(client: AsyncClient, async_session: AsyncSession):
    """Test the admin endpoint to expire old move offers."""
    # Create a clinic for the test
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={"operating_hours": {"start": "09:00", "end": "17:00"}},
    )
    async_session.add(clinic)
    await async_session.commit()

    # Create a dentist for the test
    dentist = Dentist(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Dr. Smith",
        specializations=[],
        is_active=True,
    )
    async_session.add(dentist)
    await async_session.commit()

    # Create a pending offer that has expired (25 hours ago)
    expired_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.DISCOUNT,
        incentive_value="10% discount",
        move_score=75.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(hours=25),
        expires_at=datetime.now() - timedelta(hours=1),
    )

    # Create a pending offer that hasn't expired yet
    active_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.PRIORITY_SLOT,
        incentive_value="priority slot",
        move_score=80.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(hours=1),
        expires_at=datetime.now() + timedelta(hours=23),
    )

    # Create an already expired offer
    already_expired = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.GIFT,
        incentive_value="gift card",
        move_score=60.0,
        status=MoveOfferStatus.EXPIRED,
        offered_at=datetime.now() - timedelta(hours=48),
        expires_at=datetime.now() - timedelta(hours=24),
    )

    async_session.add_all([expired_offer, active_offer, already_expired])
    await async_session.commit()

    # Call the admin endpoint to expire old offers
    response = await client.post("/admin/offers/expire")

    assert response.status_code == 200
    data = response.json()
    assert data["expired_count"] == 1
    assert "Expired 1 move offers" in data["message"]

    # Verify the expired offer is now marked as EXPIRED
    result = await async_session.execute(select(MoveOffer).where(MoveOffer.id == expired_offer.id))
    updated_expired_offer = result.scalar_one()
    assert updated_expired_offer.status == MoveOfferStatus.EXPIRED

    # Verify the active offer is still pending
    result = await async_session.execute(select(MoveOffer).where(MoveOffer.id == active_offer.id))
    updated_active_offer = result.scalar_one()
    assert updated_active_offer.status == MoveOfferStatus.PENDING

    # Verify the already expired offer is still expired
    result = await async_session.execute(select(MoveOffer).where(MoveOffer.id == already_expired.id))
    still_expired_offer = result.scalar_one()
    assert still_expired_offer.status == MoveOfferStatus.EXPIRED


@pytest.mark.asyncio
async def test_get_pending_offers_endpoint(client: AsyncClient, async_session: AsyncSession):
    """Test the admin endpoint to get pending move offers."""
    # Create a clinic for the test
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={"operating_hours": {"start": "09:00", "end": "17:00"}},
    )
    async_session.add(clinic)
    await async_session.commit()

    # Create a dentist for the test
    dentist = Dentist(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Dr. Smith",
        specializations=[],
        is_active=True,
    )
    async_session.add(dentist)
    await async_session.commit()

    # Create some offers with different statuses
    pending_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.DISCOUNT,
        incentive_value="10% discount",
        move_score=75.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(hours=1),
        expires_at=datetime.now() + timedelta(hours=23),
    )

    expired_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.PRIORITY_SLOT,
        incentive_value="priority slot",
        move_score=80.0,
        status=MoveOfferStatus.EXPIRED,
        offered_at=datetime.now() - timedelta(days=2),
        expires_at=datetime.now() - timedelta(days=1),
    )

    accepted_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=uuid4(),
        incentive_type=IncentiveType.GIFT,
        incentive_value="gift card",
        move_score=85.0,
        status=MoveOfferStatus.ACCEPTED,
        offered_at=datetime.now() - timedelta(hours=1),
        expires_at=datetime.now() + timedelta(hours=23),
    )

    async_session.add_all([pending_offer, expired_offer, accepted_offer])
    await async_session.commit()

    # Call the admin endpoint to get pending offers
    response = await client.get("/admin/offers/pending")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    offer_data = data[0]
    assert offer_data["id"] == str(pending_offer.id)
    assert offer_data["status"] == "PENDING"
    assert offer_data["incentive_value"] == "10% discount"


@pytest.mark.asyncio
async def test_get_expired_offers_endpoint(client: AsyncClient, async_session: AsyncSession):
    """Test the admin endpoint to get expired move offers."""
    # Create a clinic for the test
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        api_key="test_key",
        timezone="Australia/Sydney",
        settings={"operating_hours": {"start": "09:00", "end": "17:00"}},
    )
    async_session.add(clinic)
    await async_session.commit()

    # Create a dentist for the test
    dentist = Dentist(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Dr. Smith",
        specializations=[],
        is_active=True,
    )
    async_session.add(dentist)
    await async_session.commit()

    # Create some offers with different statuses
    pending_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.DISCOUNT,
        incentive_value="10% discount",
        move_score=75.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(hours=1),
        expires_at=datetime.now() + timedelta(hours=23),
    )

    expired_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.PRIORITY_SLOT,
        incentive_value="priority slot",
        move_score=80.0,
        status=MoveOfferStatus.EXPIRED,
        offered_at=datetime.now() - timedelta(days=2),
        expires_at=datetime.now() - timedelta(days=1),
    )

    accepted_offer = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=uuid4(),
        incentive_type=IncentiveType.GIFT,
        incentive_value="gift card",
        move_score=85.0,
        status=MoveOfferStatus.ACCEPTED,
        offered_at=datetime.now() - timedelta(hours=1),
        expires_at=datetime.now() + timedelta(hours=23),
    )

    async_session.add_all([pending_offer, expired_offer, accepted_offer])
    await async_session.commit()

    # Call the admin endpoint to get expired offers
    response = await client.get("/admin/offers/expired")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    offer_data = data[0]
    assert offer_data["id"] == str(expired_offer.id)
    assert offer_data["status"] == "EXPIRED"
    assert offer_data["incentive_value"] == "priority slot"