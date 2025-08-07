import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health_check():
    """Test basic health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_message():
    """Test sending a chat message"""
    response = client.post(
        "/api/chat/message",
        json={
            "session_id": "test-session-123",
            "message": "Hello, I need help with waste collection",
            "user_context": {"location": "Westlands"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "session_id" in data
    assert data["session_id"] == "test-session-123"

def test_create_incident():
    """Test creating an incident"""
    response = client.post(
        "/api/incidents",
        json={
            "title": "Test broken street light",
            "description": "Street light is not working on Test Road",
            "category": "street_lighting",
            "location_text": "Test Road, near Test Building",
            "contact_email": "test@example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert "status" in data
    assert data["status"] == "NEW"
    
    # Store incident ID for status check test
    return data["incident_id"]

def test_get_incident_status():
    """Test getting incident status"""
    # First create an incident
    incident_id = test_create_incident()
    
    # Then check its status
    response = client.get(f"/api/incidents/{incident_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == incident_id
    assert data["status"] == "NEW"
    assert "history" in data

def test_kb_search():
    """Test knowledge base search"""
    response = client.get("/api/kb/search?query=waste collection&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_invalid_incident_id():
    """Test getting status for non-existent incident"""
    response = client.get("/api/incidents/INVALID-ID/status")
    assert response.status_code == 404