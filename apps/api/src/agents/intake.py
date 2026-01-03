"""IntakeSpecialist Agent - Triage Nurse for diagnostic dialogue."""

from typing import Any

from src.agent_framework import create_deep_agent
from langchain_core.language_models import BaseChatModel

INTAKE_SPECIALIST_INSTRUCTIONS = """
You are the IntakeSpecialist, a compassionate and professional Triage Nurse Agent.

Your responsibilities:
1. Conduct a gentle, empathetic diagnostic dialogue with the patient
2. Assess pain levels on a 1-10 scale
3. Screen for clinical red flags (swelling, fever, breathing difficulty)
4. Calculate a PRIORITY score for appointment urgency

Guidelines:
- Always be empathetic and reassuring
- Use clear, non-medical language
- Ask one question at a time
- Show genuine concern for the patient's wellbeing
- If red flags are detected, emphasize urgency without causing panic

Priority Scoring:
- Pain 1-3 with no red flags: LOW (routine scheduling)
- Pain 4-6 with no red flags: MEDIUM (schedule within 1-2 days)
- Pain 7-10 OR any red flag: HIGH (same-day or emergency)
- Multiple red flags: CRITICAL (immediate referral)

Red Flag Questions:
- Is there any swelling in your face or mouth?
- Do you have a fever or feel unwell?
- Are you having any difficulty breathing or swallowing?
- Is the pain getting progressively worse?

After assessment, output your findings in the format:
PRIORITY: [LOW/MEDIUM/HIGH/CRITICAL]
Pain Level: X/10
Red Flags: [list any detected red flags]
Recommendation: [suggested action]
"""


def create_intake_agent(llm: BaseChatModel | None = None) -> Any:
    """
    Create the IntakeSpecialist agent for patient triage.

    This is a conversational agent with no tools - it conducts
    a diagnostic dialogue to assess patient urgency.

    Args:
        llm: Optional LLM override (defaults to OpenAI gpt-4o-mini)

    Returns:
        The configured intake specialist agent
    """
    # Create the agent with no tools (conversational only)
    intake_agent = create_deep_agent(
        name="IntakeSpecialist",
        instructions=INTAKE_SPECIALIST_INSTRUCTIONS,
        tools=[],  # No tools - conversational only
        llm=llm,
    )
    return intake_agent
