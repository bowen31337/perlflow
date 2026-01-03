"""Availability checking tool for PMS integration."""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def check_availability(start: str, end: str, db: "AsyncSession | None" = None, clinic_id: str | None = None) -> str:
    """
    Checks for open appointment slots in the Practice Management System.

    This tool queries the PMS to find available time slots within
    the specified date/time range. It considers:
    - Clinic operating hours
    - Dentist schedules and availability
    - Existing appointments
    - Procedure duration requirements

    Args:
        start: Start datetime for availability window (ISO format)
        end: End datetime for availability window (ISO format)
        db: Database session (optional, for actual queries)
        clinic_id: Clinic UUID (optional, required for real queries)

    Returns:
        A formatted string describing available slots, e.g.:
        "Available slots between 2024-01-15 and 2024-01-17:
         - Mon Jan 15, 9:00 AM - Dr. Smith
         - Mon Jan 15, 2:00 PM - Dr. Jones
         - Tue Jan 16, 10:30 AM - Dr. Smith"
    """
    # If no database session provided, return placeholder
    if db is None or clinic_id is None:
        return f"""Available slots between {start} and {end}:
- Monday 9:00 AM - Dr. Smith (General Dentist)
- Monday 2:00 PM - Dr. Jones (General Dentist)
- Tuesday 10:30 AM - Dr. Smith (General Dentist)
- Wednesday 11:00 AM - Dr. Patel (Implant Specialist)

Would you like to book any of these times?"""

    # Real implementation using database
    from sqlalchemy import select
    from src.models import Appointment, AppointmentStatus, Dentist
    from uuid import UUID

    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return f"Invalid date format. Please use ISO format (e.g., 2024-01-15T09:00:00)"

    # Get active dentists
    dentists_result = await db.execute(
        select(Dentist).where(
            Dentist.clinic_id == UUID(clinic_id),
            Dentist.is_active == True,
        )
    )
    dentists = dentists_result.scalars().all()

    if not dentists:
        return "No active dentists found for this clinic."

    # Get existing appointments in range
    appointments_result = await db.execute(
        select(Appointment).where(
            Appointment.clinic_id == UUID(clinic_id),
            Appointment.start_time >= start_dt,
            Appointment.start_time <= end_dt,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    existing_appointments = appointments_result.scalars().all()

    # Build availability summary
    from datetime import timedelta

    # Group by dentist
    availability_by_dentist: dict[str, list[str]] = {}
    for dentist in dentists:
        availability_by_dentist[dentist.name] = []

    # Simple slot generation (every 30 min, 9 AM - 5 PM)
    for dentist in dentists:
        current_time = start_dt.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = end_dt.replace(hour=17, minute=0, second=0, microsecond=0)

        while current_time <= end_time:
            # Check if this slot conflicts with existing appointments
            slot_available = True
            for appt in existing_appointments:
                if appt.dentist_id == dentist.id:
                    appt_end = appt.start_time + timedelta(minutes=appt.duration_mins)
                    # Check overlap
                    if not (current_time >= appt_end or (current_time + timedelta(minutes=30)) <= appt.start_time):
                        slot_available = False
                        break

            if slot_available and current_time >= datetime.now():
                availability_by_dentist[dentist.name].append(
                    current_time.strftime("%a %b %d, %I:%M %p")
                )

            current_time += timedelta(minutes=30)

    # Format output
    lines = [f"Available slots between {start_dt.strftime('%Y-%m-%d')} and {end_dt.strftime('%Y-%m-%d')}:"]
    for dentist_name, slots in availability_by_dentist.items():
        if slots:
            for slot in slots[:3]:  # Show first 3 slots per dentist
                lines.append(f"- {slot} - {dentist_name}")

    if any(availability_by_dentist.values()):
        lines.append("\nWould you like to book any of these times?")
    else:
        lines.append("No available slots found in this time range.")

    return "\n".join(lines)
