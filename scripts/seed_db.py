#!/usr/bin/env python3
"""Seed database with initial test data."""

import asyncio

from sqlalchemy import select

from src.core.database import async_session, init_db
from src.models import Clinic


async def seed_database() -> None:
    """Initialize database and seed test data."""
    # First, create all tables
    print("Creating database tables...")
    await init_db()
    print("✓ Database tables created")
    print()

    # Create test clinic
    async with async_session() as session:
        # Check if clinic already exists
        result = await session.execute(
            select(Clinic).where(Clinic.name == "Test Clinic")
        )
        existing_clinic = result.scalar_one_or_none()

        if existing_clinic:
            print(f"✓ Clinic '{existing_clinic.name}' already exists")
            return

        # Create test clinic
        clinic = Clinic(
            name="Test Clinic",
            timezone="Australia/Sydney",
            settings={
                "operating_hours": {
                    "monday": {"start": "09:00", "end": "17:00"},
                    "tuesday": {"start": "09:00", "end": "17:00"},
                    "wednesday": {"start": "09:00", "end": "17:00"},
                    "thursday": {"start": "09:00", "end": "17:00"},
                    "friday": {"start": "09:00", "end": "17:00"},
                    "saturday": {"start": "09:00", "end": "13:00"},
                    "sunday": None,
                },
                "slot_duration_minutes": 30,
            },
            api_key="pf_test_demo_key_12345",
        )

        session.add(clinic)
        await session.commit()
        await session.refresh(clinic)

        print(f"✓ Created clinic: {clinic.name}")
        print(f"  API Key: {clinic.api_key}")
        print(f"  Clinic ID: {clinic.id}")


async def main() -> None:
    """Main seed function."""
    print("🌱 Seeding database...")
    print()

    await seed_database()

    print()
    print("✅ Database seeding complete!")
    print()
    print("You can now use the API key: pf_test_demo_key_12345")


if __name__ == "__main__":
    asyncio.run(main())
