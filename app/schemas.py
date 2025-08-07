# app/schemas.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class IncidentStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class MessageSender(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

# Base schemas
class Citation(BaseModel):
    title: str
    snippet: str
    source_link: Optional[str] = None
    doc_id: Optional[str] = None

class UserContext(BaseModel):
    location: Optional[str] = None
    ward: Optional[str] = None
    language: Optional[str] = "en"

class LocationCoords(BaseModel):
    lat: float
    lng: float

# Chat schemas
class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_context: Optional[UserContext] = None

class ChatResponse(BaseModel):
    reply: str
    citations: List[Citation] = []
    confidence: float
    steps: Optional[List[str]] = None
    session_id: str
    requires_clarification: bool = False
    clarification_question: Optional[str] = None

class ChatMessage(BaseModel):
    id: str
    sender: MessageSender
    content: str
    citations: List[Citation] = []
    confidence: Optional[float] = None
    created_at: datetime

class ChatHistory(BaseModel):
    session_id: str
    messages: List[ChatMessage]

# Incident schemas
class IncidentRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., min_length=2, max_length=50)
    location_text: Optional[str] = Field(None, max_length=500)
    location_coords: Optional[LocationCoords] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]{10,20}$')
    photo_url: Optional[str] = None
    
    @validator('category')
    def validate_category(cls, v):
        allowed = ['road_maintenance', 'waste_management', 'water_supply', 'electricity', 'street_lighting', 'drainage', 'other']
        if v.lower() not in allowed:
            raise ValueError(f'Category must be one of: {", ".join(allowed)}')
        return v.lower()

class IncidentResponse(BaseModel):
    incident_id: str
    status: str
    created_at: datetime

class IncidentHistoryItem(BaseModel):
    status: IncidentStatus
    notes: Optional[str]
    staff_id: Optional[str]
    created_at: datetime

class IncidentStatusResponse(BaseModel):
    incident_id: str
    status: IncidentStatus
    last_update: datetime
    history: List[IncidentHistoryItem]
    title: str
    description: str
    category: str

class IncidentListItem(BaseModel):
    incident_id: str
    title: str
    category: str
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    priority: str

class IncidentDetail(BaseModel):
    incident_id: str
    title: str
    description: str
    category: str
    location_text: Optional[str]
    location_coords: Optional[LocationCoords]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    photo_url: Optional[str]
    status: IncidentStatus
    priority: str
    created_at: datetime
    updated_at: datetime
    history: List[IncidentHistoryItem]

class IncidentUpdateRequest(BaseModel):
    status: Optional[IncidentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    priority: Optional[str] = Field(None, pattern=r'^(LOW|MEDIUM|HIGH|URGENT)$')

# Knowledge Base schemas
class KBSearchResult(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float
    source_url: Optional[str] = None

class KBDocumentRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=50)
    tags: List[str] = []
    source_url: Optional[str] = None

class KBDocument(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    source_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    indexed_at: Optional[datetime]

class KBReindexResponse(BaseModel):
    indexed_docs: int
    indexed_chunks: int
    status: str
    timestamp: datetime

# Health and status schemas
class ServiceHealth(BaseModel):
    ready: bool
    status: str
    version: Optional[str] = None
    model_name: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Optional[Dict[str, ServiceHealth]] = None

# Error schemas
class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Feedback schemas
class FeedbackRequest(BaseModel):
    message_id: str
    is_helpful: bool
    comment: Optional[str] = Field(None, max_length=500)

# Notification schemas
class NotificationRequest(BaseModel):
    recipient: str
    subject: str
    content: str
    template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

# AI Service schemas
class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

class ChatCompletionRequest(BaseModel):
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7
    model: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    response: str
    model: str
    usage: Dict[str, int]