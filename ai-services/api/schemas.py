"""
Pydantic models for API request/response schemas.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class Citation(BaseModel):
    """Citation model for sources."""
    title: str = Field(..., description="Title of the source document")
    snippet: str = Field(..., description="Relevant text snippet from the source")
    source_link: Optional[str] = Field(None, description="URL or reference to the source")
    page: Optional[int] = Field(None, description="Page number if applicable")

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User's message/query")
    conversation_id: Optional[str] = Field(
        None, 
        description="Optional conversation ID for multi-turn conversations"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for the conversation"
    )

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    reply: str = Field(..., description="The generated response")
    citations: List[Citation] = Field(
        default_factory=list, 
        description="List of citations supporting the response"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score of the response (0.0 to 1.0)"
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether the system needs clarification to provide a better answer"
    )
    clarification_question: Optional[str] = Field(
        None,
        description="Follow-up question if clarification is needed"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for continuing the conversation"
    )

class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ServiceHealth(BaseModel):
    """Health status of a service component."""
    status: HealthStatus
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp of the health check"
    )

class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: HealthStatus
    version: str = Field(..., description="Service version")
    models: Dict[str, ServiceHealth] = Field(
        ...,
        description="Health status of ML models"
    )
    services: Dict[str, ServiceHealth] = Field(
        ...,
        description="Health status of service components"
    )
    timestamp: str = Field(
        ...,
        description="Server timestamp in ISO format"
    )

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
