#!/usr/bin/env python
"""Initialize SQLite database with test data."""

import asyncio
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, '.')

from sqlalchemy import select
from src.core.database import init_db, async_session
from src.models import Clinic


async def create_test_clinic():
    """Create a test clinic for development."""
    async with async_session() as db:
        # Check if clinic already exists
        result = await db.execute(
            select(Clinic).where(Clinic.api_key == "pf_test_123456")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Test clinic already exists: {existing.name}")
            return existing

        # Create test clinic
        clinic = Clinic(
            name="Pearl Dental Test Clinic",
            timezone="Australia/Sydney",
            api_key="pf_test_123456",
            settings={
                "operating_hours": {
                    "monday": {"start": "09:00", "end": "17:00"},
                    "tuesday": {"start": "09:00", "end": "17:00"},
                    "wednesday": {"start": "09:00", "end": "17:00"},
                    "thursday": {"start": "09:00", "end": "17:00"},
                    "friday": {"start": "09:00", "end": "17:00"},
                },
                "slot_duration_mins": 30,
            },
        )

        db.add(clinic)
        await db.commit()
        await db.refresh(clinic)

        print(f"Created test clinic: {clinic.name} (ID: {clinic.id})")
        print(f"API Key: {clinic.api_key}")
        return clinic


async def main():
    """Main initialization function."""
    print("🦷 Initializing PearlFlow Database...")

    # Initialize database tables
    print("Creating database tables...")
    await init_db()
    print("✓ Tables created")

    # Create test clinic
    print("\nCreating test clinic...")
    await create_test_clinic()

    print("\n✅ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
