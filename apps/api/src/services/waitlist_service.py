"""
Waitlist service for managing patient waitlist entries.
"""

from typing import Dict, List, Optional


class WaitlistService:
    """Service for waitlist management operations."""

    def __init__(self):
        self.waitlist_entries = []
        self.next_position = 1

    async def add_to_waitlist(
        self,
        patient_id: str,
        clinic_id: str,
        preferred_date_range: Optional[Dict] = None,
        preferred_time: Optional[str] = None,
        procedure_code: Optional[str] = None,
        priority_score: int = 0
    ) -> Dict:
        """
        Add a patient to the waitlist.

        Returns:
            Dict with waitlist_id and position
        """
        waitlist_id = f"wl_{len(self.waitlist_entries) + 1}"

        entry = {
            'id': waitlist_id,
            'patient_id': patient_id,
            'clinic_id': clinic_id,
            'preferred_date_range': preferred_date_range,
            'preferred_time': preferred_time,
            'procedure_code': procedure_code,
            'priority_score': priority_score,
            'status': 'active',
            'notified': False,
            'position': self.next_position
        }

        self.waitlist_entries.append(entry)
        self.next_position += 1

        return {
            'waitlist_id': waitlist_id,
            'position': entry['position']
        }

    async def get_waitlist_by_clinic(self, clinic_id: str) -> List[Dict]:
        """Get all active waitlist entries for a clinic."""
        return [
            entry for entry in self.waitlist_entries
            if entry['clinic_id'] == clinic_id and entry['status'] == 'active'
        ]

    async def notify_patient(self, waitlist_id: str) -> bool:
        """
        Notify patient that a slot is available.

        Returns:
            bool: Success status
        """
        for entry in self.waitlist_entries:
            if entry['id'] == waitlist_id:
                entry['notified'] = True
                return True
        return False

    async def update_response(self, waitlist_id: str, response: str) -> bool:
        """
        Update patient response to notification.

        Args:
            waitlist_id: Waitlist entry ID
            response: Patient response (accepted, declined, no_response)

        Returns:
            bool: Success status
        """
        for entry in self.waitlist_entries:
            if entry['id'] == waitlist_id:
                entry['response'] = response
                if response in ['accepted', 'declined']:
                    entry['status'] = 'filled'
                return True
        return False


# Singleton instance
waitlist_service = WaitlistService()
