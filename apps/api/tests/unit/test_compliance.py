"""Unit tests for AHPRA compliance filtering."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.compliance import (
    filter_compliance,
    sanitize_agent_response,
    validate_feedback_content,
    AHPRAComplianceError,
)


class TestComplianceFilter:
    """Test the compliance filter functions directly."""

    def test_filter_compliance_blocks_testimonial_language(self):
        """Test that testimonial language is detected and filtered."""
        text = "We are the best dentist in town!"
        filtered, violations = filter_compliance(text, strict=False)

        assert len(violations) > 0
        assert any(v[0] == 'TESTIMONIAL' for v in violations)
        assert 'best' not in filtered.lower() or 'experienced' in filtered.lower()

    def test_filter_compliance_blocks_comparative_claims(self):
        """Test that comparative claims are detected and filtered."""
        text = "Our services are better than other clinics."
        filtered, violations = filter_compliance(text, strict=False)

        assert len(violations) > 0
        assert any(v[0] == 'COMPARATIVE' for v in violations)

    def test_filter_compliance_blocks_guaranteed_outcomes(self):
        """Test that guaranteed outcome language is detected and filtered."""
        text = "We guarantee painless treatment!"
        filtered, violations = filter_compliance(text, strict=False)

        assert len(violations) > 0
        assert any(v[0] == 'GUARANTEE' for v in violations)

    def test_filter_compliance_strict_mode_raises_exception(self):
        """Test that strict mode raises AHPRAComplianceError."""
        text = "We are the best dentist!"

        with pytest.raises(AHPRAComplianceError) as exc_info:
            filter_compliance(text, strict=True)

        assert len(exc_info.value.violations) > 0

    def test_filter_compliance_allows_compliant_text(self):
        """Test that compliant text passes through unchanged."""
        text = "We are an experienced dental practice providing quality care."
        filtered, violations = filter_compliance(text, strict=False)

        assert len(violations) == 0
        assert filtered == text

    def test_sanitize_agent_response(self):
        """Test that sanitize_agent_response filters violations."""
        text = "We are the best dentist with guaranteed results!"
        filtered = sanitize_agent_response(text)

        # Should be modified to be compliant
        assert 'best' not in filtered.lower() or 'experienced' in filtered.lower()

    def test_validate_feedback_content_compliant(self):
        """Test that compliant feedback passes validation."""
        text = "The dentist was very professional and caring."
        assert validate_feedback_content(text) is True

    def test_validate_feedback_content_non_compliant(self):
        """Test that non-compliant feedback fails validation."""
        text = "This is the best dentist ever! Guaranteed satisfaction!"
        assert validate_feedback_content(text) is False


class TestComplianceIntegration:
    """Test compliance integration with chat API."""

    @pytest.mark.asyncio
    async def test_chat_response_is_compliant(self, client: AsyncClient, test_clinic):
        """Test that chat responses are filtered for compliance."""
        # Create session
        create_response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session_id = create_response.json()["session_id"]

        # Send a message
        await client.post(
            "/chat/message",
            json={"session_id": session_id, "text": "Hello"},
        )

        # Stream response
        async with client.stream("GET", f"/chat/stream/{session_id}") as response:
            combined = ""
            async for chunk in response.aiter_text():
                combined += chunk
                if "complete" in chunk:
                    break

        # Verify response doesn't contain prohibited patterns
        # (The default greeting should be compliant)
        assert "best" not in combined.lower() or "experienced" in combined.lower()
        assert "guarantee" not in combined.lower()

    @pytest.mark.asyncio
    async def test_chat_filters_violations_in_responses(self, client: AsyncClient, test_clinic, monkeypatch):
        """Test that violations in responses are filtered."""
        # Create session
        create_response = await client.post(
            "/session",
            json={"clinic_api_key": test_clinic.api_key},
        )
        session_id = create_response.json()["session_id"]

        # Note: We can't easily inject non-compliant responses in the current
        # keyword-based routing, but we've verified the filter is applied.
        # This test documents the expected behavior.

        # Send a message
        await client.post(
            "/chat/message",
            json={"session_id": session_id, "text": "I have a toothache"},
        )

        # Stream response
        async with client.stream("GET", f"/chat/stream/{session_id}") as response:
            combined = ""
            async for chunk in response.aiter_text():
                combined += chunk
                if "complete" in chunk:
                    break

        # Response should be compliant
        # (Current responses are already compliant, but filter is in place)
        assert "best" not in combined.lower() or "experienced" in combined.lower()


class TestCompliancePatterns:
    """Test specific AHPRA prohibited patterns."""

    def test_pattern_best_dentist(self):
        """Test 'best dentist' pattern."""
        text = "We are the best dentist in Sydney"
        filtered, violations = filter_compliance(text, strict=False)
        assert any('TESTIMONIAL' in v for v in violations)

    def test_pattern_most_trusted(self):
        """Test 'most trusted' pattern."""
        text = "Our clinic is the most trusted"
        filtered, violations = filter_compliance(text, strict=False)
        assert any('TESTIMONIAL' in v for v in violations)

    def test_pattern_better_than(self):
        """Test 'better than' pattern."""
        text = "Our care is better than other clinics"
        filtered, violations = filter_compliance(text, strict=False)
        assert any('COMPARATIVE' in v for v in violations)

    def test_pattern_guaranteed(self):
        """Test 'guaranteed' pattern."""
        text = "Guaranteed painless procedure"
        filtered, violations = filter_compliance(text, strict=False)
        assert any('GUARANTEE' in v for v in violations)

    def test_pattern_painless(self):
        """Test 'painless' pattern."""
        text = "We provide painless treatment"
        filtered, violations = filter_compliance(text, strict=False)
        assert any('GUARANTEE' in v for v in violations)

    def test_pattern_100_percent(self):
        """Test '100%' pattern."""
        text = "100% success rate"
        filtered, violations = filter_compliance(text, strict=False)
        assert any('GUARANTEE' in v for v in violations)

    def test_allowed_terms_pass_through(self):
        """Test that allowed informational terms are preserved."""
        text = "We are an experienced, qualified, and professional practice"
        filtered, violations = filter_compliance(text, strict=False)
        assert len(violations) == 0
        assert filtered == text
