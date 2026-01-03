"""Tests for move offer expiration functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MoveOffer, MoveOfferStatus, IncentiveType
from src.services.move_offer_service import MoveOfferService


@pytest.mark.asyncio
async def test_expire_old_offers_service(async_session: AsyncSession):
    """Test the MoveOfferService expire_old_offers method."""
    service = MoveOfferService(async_session)

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

    # Run the expiration job
    expired_count = await service.expire_old_offers()

    # Should have expired 1 offer (the one that was pending but expired)
    assert expired_count == 1

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
async def test_expire_old_offers_no_expired_offers(async_session: AsyncSession):
    """Test expiring offers when none have expired."""
    service = MoveOfferService(async_session)

    # Create offers that haven't expired yet
    offer1 = MoveOffer(
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

    offer2 = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.PRIORITY_SLOT,
        incentive_value="priority slot",
        move_score=80.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(hours=2),
        expires_at=datetime.now() + timedelta(hours=22),
    )

    async_session.add_all([offer1, offer2])
    await async_session.commit()

    # Run the expiration job
    expired_count = await service.expire_old_offers()

    # Should have expired 0 offers
    assert expired_count == 0

    # Verify both offers are still pending
    result = await async_session.execute(select(MoveOffer).where(MoveOffer.id.in_([offer1.id, offer2.id])))
    offers = result.scalars().all()
    for offer in offers:
        assert offer.status == MoveOfferStatus.PENDING


@pytest.mark.asyncio
async def test_expire_old_offers_all_expired(async_session: AsyncSession):
    """Test expiring offers when all have expired."""
    service = MoveOfferService(async_session)

    # Create offers that have all expired
    offer1 = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.DISCOUNT,
        incentive_value="10% discount",
        move_score=75.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(days=2),
        expires_at=datetime.now() - timedelta(days=1),
    )

    offer2 = MoveOffer(
        id=uuid4(),
        original_appointment_id=uuid4(),
        target_appointment_id=None,
        incentive_type=IncentiveType.PRIORITY_SLOT,
        incentive_value="priority slot",
        move_score=80.0,
        status=MoveOfferStatus.PENDING,
        offered_at=datetime.now() - timedelta(days=3),
        expires_at=datetime.now() - timedelta(days=2),
    )

    async_session.add_all([offer1, offer2])
    await async_session.commit()

    # Run the expiration job
    expired_count = await service.expire_old_offers()

    # Should have expired 2 offers
    assert expired_count == 2

    # Verify both offers are now expired
    result = await async_session.execute(select(MoveOffer).where(MoveOffer.id.in_([offer1.id, offer2.id])))
    offers = result.scalars().all()
    for offer in offers:
        assert offer.status == MoveOfferStatus.EXPIRED


@pytest.mark.asyncio
async def test_get_pending_offers(async_session: AsyncSession):
    """Test retrieving pending offers."""
    service = MoveOfferService(async_session)

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

    # Get pending offers
    pending_offers = await service.get_pending_offers()

    # Should only return the pending offer
    assert len(pending_offers) == 1
    assert pending_offers[0].id == pending_offer.id
    assert pending_offers[0].status == MoveOfferStatus.PENDING


@pytest.mark.asyncio
async def test_get_expired_offers(async_session: AsyncSession):
    """Test retrieving expired offers."""
    service = MoveOfferService(async_session)

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

    # Get expired offers
    expired_offers = await service.get_expired_offers()

    # Should only return the expired offer
    assert len(expired_offers) == 1
    assert expired_offers[0].id == expired_offer.id
    assert expired_offers[0].status == MoveOfferStatus.EXPIRED