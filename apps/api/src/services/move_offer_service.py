"""Move offer service for handling appointment rescheduling incentives."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MoveOffer, MoveOfferStatus


class MoveOfferService:
    """Service for handling move offer operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def expire_old_offers(self) -> int:
        """
        Expire move offers that have passed their expiration time.

        Returns:
            int: Number of offers that were expired
        """
        # Find offers that are still pending and have expired
        current_time = datetime.now()
        result = await self.db.execute(
            select(MoveOffer.id).where(
                MoveOffer.status == MoveOfferStatus.PENDING,
                MoveOffer.expires_at < current_time
            )
        )
        expired_offer_ids = result.scalars().all()

        if not expired_offer_ids:
            return 0

        # Update the status of expired offers and set responded_at
        await self.db.execute(
            update(MoveOffer)
            .where(MoveOffer.id.in_(expired_offer_ids))
            .values(
                status=MoveOfferStatus.EXPIRED,
                responded_at=current_time,
            )
        )

        await self.db.commit()
        return len(expired_offer_ids)

    async def get_pending_offers(self):
        """Get all pending move offers."""
        result = await self.db.execute(
            select(MoveOffer).where(
                MoveOffer.status == MoveOfferStatus.PENDING
            ).order_by(MoveOffer.expires_at.asc())
        )
        return result.scalars().all()

    async def get_expired_offers(self):
        """Get all expired move offers."""
        result = await self.db.execute(
            select(MoveOffer).where(
                MoveOffer.status == MoveOfferStatus.EXPIRED
            ).order_by(MoveOffer.expires_at.asc())
        )
        return result.scalars().all()