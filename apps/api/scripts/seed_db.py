#!/usr/bin/env python3
"""Seed database with test data."""

import asyncio
import uuid

from sqlalchemy import select

from src.core.database import async_session
from src.models import Clinic


async def seed_database() -> None:
    """Seed database with initial test data."""
    async with async_session() as session:
        # Check if clinic already exists
        result = await session.execute(select(Clinic).where(Clinic.name == "Test Clinic"))
        existing_clinic = result.scalar_one_or_none()

        if existing_clinic:
            print(f"Clinic already exists: {existing_clinic.name} (API Key: {existing_clinic.api_key})")
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
                },
                "slot_duration_mins": 30,
            },
            api_key="pf_test_" + str(uuid.uuid4()),
        )

        session.add(clinic)
        await session.commit()
        await session.refresh(clinic)

        print(f"✅ Created test clinic:")
        print(f"   Name: {clinic.name}")
        print(f"   API Key: {clinic.api_key}")
        print(f"   ID: {clinic.id}")


if __name__ == "__main__":
    asyncio.run(seed_database())
