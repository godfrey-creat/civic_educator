from sqlalchemy import Column, String, Text, DateTime, Enum, Float, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base, engine
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import enum
from datetime import datetime

# Detect dialect and choose UUID column type
if engine.dialect.name == "sqlite":
    UUIDType = String(36)
    uuid_default = lambda: str(uuid.uuid4())
else:
    from sqlalchemy.dialects.postgresql import UUID
    UUIDType = UUID(as_uuid=True)
    uuid_default = uuid.uuid4

class IncidentStatus(enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class MessageSender(enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    session_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_context = Column(JSON)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    conversation_id = Column(UUIDType, ForeignKey("conversations.id"), nullable=False)
    sender = Column(Enum(MessageSender), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSON)
    confidence = Column(Float)
    message_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    conversation = relationship("Conversation", back_populates="messages")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    location_text = Column(String(500))
    location_coords = Column(JSON)
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    photo_url = Column(String(500))
    status = Column(Enum(IncidentStatus), default=IncidentStatus.NEW, nullable=False)
    priority = Column(String(20), default="MEDIUM")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    history = relationship("IncidentHistory", back_populates="incident", cascade="all, delete-orphan")

class IncidentHistory(Base):
    __tablename__ = "incident_history"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    status = Column(Enum(IncidentStatus), nullable=False)
    notes = Column(Text)
    staff_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    incident = relationship("Incident", back_populates="history")

class KnowledgeBaseDocument(Base):
    __tablename__ = "kb_documents"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON)
    source_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    indexed_at = Column(DateTime(timezone=True))
    chunks = relationship("KnowledgeBaseChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeBaseChunk(Base):
    __tablename__ = "kb_chunks"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    document_id = Column(UUIDType, ForeignKey("kb_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    meta = Column(JSON)
    embedding = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    document = relationship("KnowledgeBaseDocument", back_populates="chunks")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    staff_id = Column(String(100))
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    message_id = Column(UUIDType, ForeignKey("messages.id"))
    is_helpful = Column(Boolean, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_staff = Column(Boolean, default=False) 
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class Course(Base):
    __tablename__ = "courses"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    course_id = Column(UUIDType, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    course = relationship("Course", back_populates="lessons")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    lesson_id = Column(UUIDType, ForeignKey("lessons.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lesson = relationship("Lesson", back_populates="quizzes")

class Progress(Base):
    __tablename__ = "progress"
    id = Column(UUIDType, primary_key=True, default=uuid_default)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(UUIDType, ForeignKey("lessons.id"), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
