"""Root Receptionist Agent - Main orchestrator with SubAgentMiddleware."""

from typing import Any

# Note: deepagents is a custom library - this is the expected pattern
# from deepagents import create_deep_agent
# from deepagents.middleware import SubAgentMiddleware
# from langchain_core.messages import HumanMessage

from src.agents.intake import create_intake_agent
from src.agents.scheduler import create_scheduler_agent

RECEPTIONIST_INSTRUCTIONS = """
You are the Main Receptionist for a dental practice, a warm and professional
virtual assistant powered by PearlFlow.

Your responsibilities:
1. Greet patients warmly and understand their needs
2. Classify patient intent and delegate to appropriate specialists
3. Maintain a polite, helpful, and empathetic tone throughout

Intent Classification:
- PAIN/EMERGENCY: Patient mentions pain, discomfort, swelling, injury, bleeding,
  or any urgent dental issue → Delegate to 'IntakeSpecialist'
- BOOKING: Patient wants to schedule, reschedule, or inquire about appointments
  → Delegate to 'ResourceOptimiser'
- GENERAL: General questions about the practice, hours, services
  → Handle directly with helpful information

Guidelines:
- Always introduce yourself on first interaction
- Use the patient's name if known
- Be empathetic to pain or distress
- Never provide medical advice - always recommend professional evaluation
- For emergencies, stress the importance of immediate care
- Keep responses concise but warm

Example Responses:
- "I'm so sorry to hear you're in pain. Let me connect you with our triage
  specialist who can assess your situation right away."
- "I'd be happy to help you book an appointment! Let me find the best
  available times for you."
- "Our practice is open Monday through Friday, 9 AM to 5 PM. How can I
  assist you today?"

AHPRA Compliance:
- Never use testimonial language or claim to be "the best"
- Don't make comparative claims about treatment outcomes
- Always recommend professional evaluation for medical concerns
"""


def create_receptionist_agent() -> Any:
    """
    Create the root Receptionist agent with SubAgentMiddleware.

    The Receptionist is the main orchestrator that classifies patient
    intent and delegates to specialized sub-agents:
    - IntakeSpecialist: For pain/emergency triage
    - ResourceOptimiser: For appointment scheduling

    Returns:
        The configured receptionist agent with middleware
    """
    # Create sub-agents
    intake_agent = create_intake_agent()
    scheduler_agent = create_scheduler_agent()

    # TODO: Replace with actual deepagents implementation when available
    # sub_agent_middleware = SubAgentMiddleware(
    #     sub_agents=[intake_agent, scheduler_agent]
    # )

    # root_agent = create_deep_agent(
    #     name="Receptionist",
    #     instructions=RECEPTIONIST_INSTRUCTIONS,
    #     middleware=[sub_agent_middleware],
    # )
    # return root_agent

    # Placeholder return
    return {
        "name": "Receptionist",
        "instructions": RECEPTIONIST_INSTRUCTIONS,
        "sub_agents": [intake_agent, scheduler_agent],
    }


async def run_chat(user_input: str, session_id: str) -> dict[str, Any]:
    """
    Execute a chat turn with the agent system.

    Args:
        user_input: The user's message text
        session_id: The session UUID for state persistence

    Returns:
        The agent's response including messages and tool calls
    """
    # TODO: Replace with actual deepagents implementation
    # from langchain_core.messages import HumanMessage

    # root_agent = create_receptionist_agent()
    # response = await root_agent.ainvoke(
    #     {"messages": [HumanMessage(content=user_input)]},
    #     config={"configurable": {"thread_id": session_id}}
    # )
    # return response

    # Placeholder implementation
    return {
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "Hello! Welcome to PearlFlow. I'm your virtual dental assistant. "
                    "How can I help you today?"
                ),
            }
        ],
        "agent_state": {
            "active_agent": "Receptionist",
            "thinking": False,
        },
    }
