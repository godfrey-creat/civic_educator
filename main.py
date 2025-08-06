# main.py
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime
import uuid

# Import our modules
from app.database import engine, Base, get_db
from app.models import *
from app.schemas import *
from app.services.chat_service import ChatService
from app.services.incident_service import IncidentService
from app.services.kb_service import KnowledgeBaseService
from app.services.ai_service import AIService
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting CivicNavigator backend...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize AI service
    ai_service = AIService()
    await ai_service.initialize()
    app.state.ai_service = ai_service
    
    # Initialize other services
    app.state.chat_service = ChatService(ai_service)
    app.state.incident_service = IncidentService()
    app.state.kb_service = KnowledgeBaseService(ai_service)
    
    logger.info("Backend initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend...")
    if hasattr(app.state, 'ai_service'):
        await app.state.ai_service.cleanup()

app = FastAPI(
    title="CivicNavigator API",
    description="Backend API for CivicNavigator Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple authentication - extend for production"""
    if not credentials:
        return None
    
    # For demo purposes, accept any token
    # In production, validate JWT tokens properly
    token = credentials.credentials
    if token.startswith("staff_"):
        return {"user_id": token, "role": "staff"}
    elif token.startswith("resident_"):
        return {"user_id": token, "role": "resident"}
    return None

def require_staff(user=Depends(get_current_user)):
    """Require staff authentication"""
    if not user or user.get("role") != "staff":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff access required"
        )
    return user

# Health endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/ready")
async def readiness_check():
    """Readiness check including AI service"""
    try:
        ai_ready = await app.state.ai_service.health_check()
        return {
            "status": "ready" if ai_ready["ready"] else "not_ready",
            "services": {
                "ai": ai_ready,
                "database": {"ready": True, "status": "connected"}
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

# Chat endpoints
@app.post("/api/chat/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    db=Depends(get_db)
):
    """Send a chat message and get AI response"""
    try:
        response = await app.state.chat_service.process_message(
            session_id=request.session_id,
            message=request.message,
            user_context=request.user_context,
            db=db
        )
        return response
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(status_code=500, detail="Chat service error")

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db=Depends(get_db)
):
    """Get chat history for a session"""
    try:
        history = await app.state.chat_service.get_history(session_id, db)
        return {"messages": history}
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@app.delete("/api/chat/history/{session_id}")
async def delete_chat_history(
    session_id: str,
    db=Depends(get_db)
):
    """Delete chat history for privacy"""
    try:
        await app.state.chat_service.delete_history(session_id, db)
        return {"message": "Chat history deleted"}
    except Exception as e:
        logger.error(f"Delete chat history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat history")

# Incident endpoints
@app.post("/api/incidents", response_model=IncidentResponse)
async def create_incident(
    request: IncidentRequest,
    db=Depends(get_db)
):
    """Create a new incident report"""
    try:
        incident = await app.state.incident_service.create_incident(request, db)
        return IncidentResponse(
            incident_id=incident.id,
            status=incident.status.value,
            created_at=incident.created_at
        )
    except Exception as e:
        logger.error(f"Create incident error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create incident")

@app.get("/api/incidents/{incident_id}/status", response_model=IncidentStatusResponse)
async def get_incident_status(
    incident_id: str,
    db=Depends(get_db)
):
    """Get incident status and history"""
    try:
        status_info = await app.state.incident_service.get_status(incident_id, db)
        if not status_info:
            raise HTTPException(status_code=404, detail="Incident not found")
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get incident status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve incident status")

# Staff endpoints
@app.get("/api/staff/incidents", response_model=List[IncidentListItem])
async def list_incidents(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    staff_user=Depends(require_staff),
    db=Depends(get_db)
):
    """List incidents for staff (with filters)"""
    try:
        incidents = await app.state.incident_service.list_incidents(
            status=status,
            category=category,
            limit=limit,
            offset=offset,
            db=db
        )
        return incidents
    except Exception as e:
        logger.error(f"List incidents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list incidents")

@app.get("/api/staff/incidents/{incident_id}", response_model=IncidentDetail)
async def get_incident_detail(
    incident_id: str,
    staff_user=Depends(require_staff),
    db=Depends(get_db)
):
    """Get detailed incident information for staff"""
    try:
        incident = await app.state.incident_service.get_detail(incident_id, db)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get incident detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve incident")

@app.patch("/api/staff/incidents/{incident_id}")
async def update_incident(
    incident_id: str,
    request: IncidentUpdateRequest,
    staff_user=Depends(require_staff),
    db=Depends(get_db)
):
    """Update incident status and notes"""
    try:
        success = await app.state.incident_service.update_incident(
            incident_id=incident_id,
            status=request.status,
            notes=request.notes,
            staff_id=staff_user["user_id"],
            db=db
        )
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")
        return {"message": "Incident updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update incident error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update incident")

# Knowledge Base endpoints
@app.get("/api/kb/search")
async def search_kb(
    query: str,
    limit: int = 5,
    db=Depends(get_db)
):
    """Search knowledge base"""
    try:
        results = await app.state.kb_service.search(query, limit, db)
        return {"results": results}
    except Exception as e:
        logger.error(f"KB search error: {e}")
        raise HTTPException(status_code=500, detail="Knowledge base search failed")

@app.post("/api/staff/kb/documents")
async def create_kb_document(
    request: KBDocumentRequest,
    staff_user=Depends(require_staff),
    db=Depends(get_db)
):
    """Create or update a knowledge base document"""
    try:
        doc = await app.state.kb_service.create_or_update_document(
            title=request.title,
            content=request.content,
            tags=request.tags,
            source_url=request.source_url,
            db=db
        )
        return {"document_id": doc.id, "message": "Document created/updated"}
    except Exception as e:
        logger.error(f"Create KB document error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document")

@app.post("/api/staff/kb/reindex")
async def reindex_kb(
    staff_user=Depends(require_staff),
    db=Depends(get_db)
):
    """Reindex the knowledge base"""
    try:
        result = await app.state.kb_service.reindex(db)
        return result
    except Exception as e:
        logger.error(f"KB reindex error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reindex knowledge base")

@app.get("/api/staff/kb/documents")
async def list_kb_documents(
    limit: int = 50,
    offset: int = 0,
    staff_user=Depends(require_staff),
    db=Depends(get_db)
):
    """List knowledge base documents"""
    try:
        docs = await app.state.kb_service.list_documents(limit, offset, db)
        return {"documents": docs}
    except Exception as e:
        logger.error(f"List KB documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )