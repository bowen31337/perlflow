"""AHPRA compliance filtering for dental practice communications.

This module provides filtering to ensure all patient-facing communications
comply with Australian Health Practitioner Regulation Agency (AHPRA) advertising
guidelines.

AHPRA Key Restrictions:
- No testimonial language (e.g., "best dentist", "most trusted")
- No comparative claims (e.g., "better than other clinics")
- No guaranteed outcomes (e.g., "guaranteed results", "painless")
- No misleading claims about expertise or success rates
- All patient feedback requires manual approval before publication
"""

import re
from typing import List, Tuple


# AHPRA-prohibited patterns
PROHIBITED_PATTERNS = [
    # Testimonial language
    (r'\b(best|top|leading|premier|finest|ultimate|number one|#1)\b', 'TESTIMONIAL'),
    (r'\b(most trusted|most experienced|most advanced)\b', 'TESTIMONIAL'),
    (r'\b(award-winning|acclaimed|renowned)\b', 'TESTIMONIAL'),

    # Comparative claims
    (r'\b(better than|superior to|more advanced than|ahead of)\b', 'COMPARATIVE'),
    (r'\b(other clinics|other dentists|competitors)\b', 'COMPARATIVE'),

    # Guaranteed outcomes
    (r'\b(guaranteed|guarantee|promise|warranty|assured)\b', 'GUARANTEE'),
    (r'\b(painless|risk-free|no pain|no risk)\b', 'GUARANTEE'),
    (r'\b(100%|always|never fail|perfect)\b', 'GUARANTEE'),

    # Misleading expertise claims
    (r'\b(expert|specialist|leading expert) (in|on) (everything|all|any)\b', 'MISLEADING'),
    (r'\b(only clinic|only dentist|unique) (in|on) (area|region|city)\b', 'MISLEADING'),
]


# Allowed informational terms (for context)
ALLOWED_TERMS = [
    'experienced', 'qualified', 'registered', 'licensed', 'professional',
    'modern', 'advanced', 'state-of-the-art', 'comprehensive', 'personalized',
    'comfortable', 'safe', 'clean', 'friendly', 'caring', 'gentle'
]


class AHPRAComplianceError(Exception):
    """Raised when content violates AHPRA compliance guidelines."""

    def __init__(self, violations: List[Tuple[str, str, str]]):
        """
        Args:
            violations: List of (pattern_type, matched_text, context) tuples
        """
        self.violations = violations
        super().__init__(f"AHPRA compliance violations detected: {violations}")


def filter_compliance(text: str, strict: bool = True) -> Tuple[str, List[Tuple[str, str, str]]]:
    """
    Filter text for AHPRA compliance violations.

    Args:
        text: The text to filter
        strict: If True, raise exception on violations. If False, return filtered text.

    Returns:
        Tuple of (filtered_text, violations)

    Raises:
        AHPRAComplianceError: If strict=True and violations are found
    """
    violations = []
    filtered_text = text

    for pattern, violation_type in PROHIBITED_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            matched_text = match.group(0)
            # Get context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            violations.append((violation_type, matched_text, context))

            # Replace with generic alternative
            if violation_type == 'TESTIMONIAL':
                filtered_text = re.sub(
                    pattern,
                    lambda m: 'experienced' if m.group(0).lower() in ['best', 'top', 'finest'] else 'trusted',
                    filtered_text,
                    flags=re.IGNORECASE,
                    count=1
                )
            elif violation_type == 'COMPARATIVE':
                filtered_text = re.sub(
                    pattern,
                    'appropriate',
                    filtered_text,
                    flags=re.IGNORECASE,
                    count=1
                )
            elif violation_type == 'GUARANTEE':
                filtered_text = re.sub(
                    pattern,
                    'likely',
                    filtered_text,
                    flags=re.IGNORECASE,
                    count=1
                )
            elif violation_type == 'MISLEADING':
                filtered_text = re.sub(
                    pattern,
                    'experienced',
                    filtered_text,
                    flags=re.IGNORECASE,
                    count=1
                )

    if strict and violations:
        raise AHPRAComplianceError(violations)

    return filtered_text, violations


def validate_feedback_content(text: str) -> bool:
    """
    Validate patient feedback content for AHPRA compliance.

    Feedback has stricter requirements - must be manually approved.
    This function checks if feedback contains prohibited content.

    Args:
        text: Patient feedback content

    Returns:
        True if compliant (safe for approval), False if needs review
    """
    try:
        filter_compliance(text, strict=True)
        return True
    except AHPRAComplianceError:
        return False


def sanitize_agent_response(text: str) -> str:
    """
    Sanitize agent response text to ensure AHPRA compliance.

    This is used when generating responses to ensure no violations slip through.

    Args:
        text: Raw agent response

    Returns:
        Compliant response text
    """
    filtered, violations = filter_compliance(text, strict=False)

    # Log violations for monitoring
    if violations:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"AHPRA compliance filter applied: {violations}")

    return filtered
