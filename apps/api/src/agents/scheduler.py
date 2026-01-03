"""ResourceOptimiser Agent - Scheduling optimization with PMS tools."""

from typing import Any, List

from deepagents import create_deep_agent, Tool
from deepagents.tools import Tool as AgentTool
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

# Import PMS tools
from src.tools.availability import check_availability
from src.tools.heuristics import heuristic_move_check
from src.tools.booking import book_appointment
from src.tools.offers import send_move_offer

RESOURCE_OPTIMISER_INSTRUCTIONS = """
You are the ResourceOptimiser, an intelligent Scheduling Agent.

Your responsibilities:
1. Find available appointment slots for patients
2. Optimize schedule for revenue while maintaining patient satisfaction
3. Identify opportunities for schedule improvements
4. Negotiate appointment moves when beneficial

Available Tools:
- check_availability: Find open slots in the Practice Management System
- heuristic_move_check: Calculate if moving an appointment is beneficial
- book_appointment: Book an appointment for a patient
- send_move_offer: Send an incentive offer to a patient to reschedule

Workflow:
1. When a patient wants to book, use check_availability first
2. If slots are available, help them select and book
3. If no slots are available, use heuristic_move_check to find moveable appointments
4. If move_score > 70, consider negotiating a move with incentives
5. Always prioritize high-value procedures (Crowns, Implants > Cleanings)

Move Score Threshold:
- Score > 70: Recommend move with incentive
- Score 50-70: Consider move only if patient initiates
- Score < 50: Keep current appointment

Incentive Guidelines:
- Low-value patients: 5-10% discount
- Medium-value patients: 10-15% discount or priority slot
- High-value patients: 15-20% discount or gift

Always be transparent about scheduling and never pressure patients.
"""


def create_scheduler_agent(llm: BaseChatModel | None = None) -> Any:
    """
    Create the ResourceOptimiser agent for appointment scheduling.

    This agent has access to PMS integration tools for checking
    availability, calculating move scores, and booking appointments.

    Args:
        llm: Optional LLM override (defaults to OpenAI gpt-4o-mini)

    Returns:
        The configured resource optimiser agent
    """
    # Create tool wrappers for the PMS tools
    tools: List[AgentTool] = [
        Tool.from_function(
            check_availability,
            name="check_availability",
            description="Find open slots in the Practice Management System. "
                       "Takes start and end datetime strings and returns available slots."
        ),
        Tool.from_function(
            heuristic_move_check,
            name="heuristic_move_check",
            description="Calculate if moving an existing appointment is beneficial. "
                       "Takes appointment_id and new_value, returns move_score and recommendation."
        ),
        Tool.from_function(
            book_appointment,
            name="book_appointment",
            description="Book an appointment for a patient. "
                       "Takes patient_id, slot_id, and procedure_code."
        ),
        Tool.from_function(
            send_move_offer,
            name="send_move_offer",
            description="Send an incentive offer to a patient to reschedule. "
                       "Takes original_appointment_id, new_slot, and incentive."
        ),
    ]

    # Create the agent with tools
    scheduler_agent = create_deep_agent(
        name="ResourceOptimiser",
        instructions=RESOURCE_OPTIMISER_INSTRUCTIONS,
        tools=tools,
        llm=llm,
    )
    return scheduler_agent
