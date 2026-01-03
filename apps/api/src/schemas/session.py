"""Session-related Pydantic schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status enumeration."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    clinic_api_key: str = Field(..., description="Clinic API key for authentication")


class SessionResponse(BaseModel):
    """Schema for session response."""

    session_id: str = Field(..., description="Session UUID")
    status: SessionStatus = Field(..., description="Session status")
    current_agent: str = Field(..., description="Currently active agent")
    messages: list[dict[str, Any]] = Field(default_factory=list, description="Conversation history")

    class Config:
        from_attributes = True
