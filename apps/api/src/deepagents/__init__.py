"""
Deepagents - Agent orchestration library built on LangGraph.

This module provides a simplified wrapper around LangGraph to implement
the deepagents pattern for multi-agent orchestration.
"""

from typing import Any, Callable, List, Optional, Dict, Union
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import Tool as LangChainTool
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
import asyncio


__all__ = [
    "create_deep_agent",
    "SubAgentMiddleware",
    "Tool",
    "HumanMessage",
]


class Tool:
    """Wrapper for creating tools from functions."""

    @staticmethod
    def from_function(func: Callable, name: Optional[str] = None, description: Optional[str] = None) -> LangChainTool:
        """
        Create a LangChain Tool from a Python function.

        Args:
            func: The async function to wrap
            name: Optional name for the tool
            description: Optional description

        Returns:
            A LangChain Tool instance
        """
        func_name = name or func.__name__
        func_doc = description or func.__doc__ or ""

        return LangChainTool(
            name=func_name,
            description=func_doc,
            func=func,
        )


class SubAgentMiddleware:
    """
    Middleware for registering sub-agents with a root orchestrator.

    This handles the delegation logic between the root agent and sub-agents
    based on intent classification.
    """

    def __init__(self, sub_agents: List[Dict[str, Any]]):
        """
        Initialize with a list of sub-agent configurations.

        Args:
            sub_agents: List of agent dicts with 'name' and 'instructions'
        """
        self.sub_agents = {agent["name"]: agent for agent in sub_agents}

    def get_sub_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get a sub-agent by name."""
        return self.sub_agents.get(agent_name)


class DeepAgent:
    """
    A deepagent - an agent created with create_deep_agent().

    Wraps a LangGraph state graph with the deepagents interface.
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        tools: List[LangChainTool],
        middleware: Optional[SubAgentMiddleware] = None,
        llm: Optional[BaseChatModel] = None,
    ):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.middleware = middleware
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for this agent."""
        from langgraph.graph import StateGraph, END
        from typing import TypedDict, Annotated, Sequence
        import operator

        # Define state
        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], operator.add]
            active_agent: str
            thinking: bool

        # Create graph
        graph = StateGraph(AgentState)

        # Add nodes
        if self.tools:
            tool_node = ToolNode(self.tools)
            graph.add_node("tools", tool_node)

        # Add LLM node
        graph.add_node("agent", self._call_model)

        # Set entry point
        graph.set_entry_point("agent")

        # Add edges
        if self.tools:
            # Decide whether to use tools or end
            graph.add_conditional_edges(
                "agent",
                self.should_continue,
                {
                    "continue": "tools",
                    "end": END,
                }
            )
            # Tools go back to agent
            graph.add_edge("tools", "agent")
        else:
            # No tools - just agent to end
            graph.add_edge("agent", END)

        return graph.compile()

    def _call_model(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Call the LLM with the current state."""
        messages = state["messages"]

        # Add system prompt with instructions
        system_prompt = f"You are {self.name}.\n\n{self.instructions}"

        # Call LLM
        response = self.llm.invoke([HumanMessage(content=system_prompt)] + list(messages))

        return {"messages": [response]}

    def should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If the last message is an AIMessage with tool calls, continue
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        return "end"

    async def ainvoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke the agent asynchronously.

        Args:
            input_data: Input data (e.g., {"messages": [HumanMessage(...)]})
            config: Configuration with thread_id for session management

        Returns:
            Agent response
        """
        # Extract session_id from config for state persistence
        thread_id = None
        if config and "configurable" in config:
            thread_id = config["configurable"].get("thread_id")

        # Prepare initial state
        messages = input_data.get("messages", [])

        # If we have a thread_id, we should load previous state
        # (This would integrate with database checkpointing in a real implementation)

        state = {
            "messages": messages,
            "active_agent": self.name,
            "thinking": True,
        }

        # Run the graph
        try:
            result = await self.graph.ainvoke(state)

            # Extract response
            response_messages = result.get("messages", [])
            last_message = response_messages[-1] if response_messages else None

            return {
                "messages": response_messages,
                "agent_state": {
                    "active_agent": self.name,
                    "thinking": False,
                },
                "content": last_message.content if last_message else "",
            }
        except Exception as e:
            return {
                "messages": [],
                "agent_state": {
                    "active_agent": self.name,
                    "thinking": False,
                },
                "content": f"Error: {str(e)}",
            }


def create_deep_agent(
    name: str,
    instructions: str,
    tools: Optional[List[LangChainTool]] = None,
    middleware: Optional[SubAgentMiddleware] = None,
    llm: Optional[BaseChatModel] = None,
) -> DeepAgent:
    """
    Create a deepagent with the given configuration.

    This is the main entry point for creating agents in the deepagents framework.

    Args:
        name: Name of the agent
        instructions: System instructions for the agent
        tools: List of tools the agent can use
        middleware: SubAgentMiddleware for delegation
        llm: Optional LLM override

    Returns:
        A DeepAgent instance
    """
    return DeepAgent(
        name=name,
        instructions=instructions,
        tools=tools or [],
        middleware=middleware,
        llm=llm,
    )
