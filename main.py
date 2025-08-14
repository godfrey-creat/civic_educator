import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import *
from app.schemas import *
from app.services.chat_service import ChatService
from app.services.incident_service import IncidentService
from app.services.kb_service import KnowledgeBaseService
from app.services.ai_service import AIService
from app.config import settings
from app.auth import router as auth_router, decode_access_token
#from app.content import ChatRequest, ChatResponse, IncidentRequest, IncidentResponse, IncidentStatusResponse, IncidentListItem, IncidentUpdateRequest
#from app.content import IncidentResponse, ChatRequest, ChatResponse
from app.content import router as content_router
from app.api.routes.staff_kb import router as staff_kb
from app.api.deps import get_current_staff_user
# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import and alias any additional routers here
# Example:
# from app.some_module import router as some_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CivicNavigator backend...")
    Base.metadata.create_all(bind=engine)
    ai_service = AIService()
    await ai_service.initialize()
    app.state.ai_service = ai_service
    app.state.chat_service = ChatService(ai_service)
    app.state.incident_service = IncidentService()
    app.state.kb_service = KnowledgeBaseService(ai_service)
    logger.info("Backend initialized successfully")
    yield
    logger.info("Shutting down backend...")
    await ai_service.cleanup()

app = FastAPI(
    title="CivicNavigator API",
    description="Backend API for CivicNavigator Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# Routers
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(staff_kb)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Auth dependency
# ----------------------------
security = HTTPBearer(auto_error=False)

def get_current_staff_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    is_staff = payload.get("is_staff")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not is_staff:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff access required")
    
    return user

# ----------------------------
# Health Endpoints
# ----------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/ready")
async def readiness_check():
    try:
        ai_ready = await app.state.ai_service.health_check()
        return {
            "status": "ready" if ai_ready["ready"] else "not_ready",
            "services": {"ai": ai_ready, "database": {"ready": True}},
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})

# ----------------------------
# Chat Endpoints
# ----------------------------
@app.post("/api/chat/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest, db=Depends(get_db)):
    return await app.state.chat_service.process_message(
        session_id=request.session_id,
        message=request.message,
        user_context=request.user_context,
        db=db
    )

# ----------------------------
# Incident Endpoints
# ----------------------------
@app.post("/api/incidents", response_model=IncidentResponse)
async def create_incident(request: IncidentRequest, db=Depends(get_db)):
    incident = await app.state.incident_service.create_incident(request, db)
    return IncidentResponse(incident_id=incident.id, status=incident.status.value, created_at=incident.created_at)

@app.get("/api/incidents/{incident_id}/status", response_model=IncidentStatusResponse)
async def get_incident_status(incident_id: str, db=Depends(get_db)):
    status_info = await app.state.incident_service.get_status(incident_id, db)
    if not status_info:
        raise HTTPException(status_code=404, detail="Incident not found")
    return status_info

# Staff endpoints (JWT Protected)
@app.get("/api/staff/incidents", response_model=List[IncidentListItem])
async def list_incidents(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    staff_user=Depends(get_current_staff_user),
    db=Depends(get_db)
):
    return await app.state.incident_service.list_incidents(
        status=status, category=category, limit=limit, offset=offset, db=db
    )

@app.patch("/api/staff/incidents/{incident_id}")
async def update_incident(
    incident_id: str,
    request: IncidentUpdateRequest,
    staff_user=Depends(get_current_staff_user),
    db=Depends(get_db)
):
    success = await app.state.incident_service.update_incident(
        incident_id=incident_id,
        status=request.status,
        notes=request.notes,
        staff_id=staff_user.id,  # now uses SQLAlchemy object
        db=db
    )
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident updated successfully"}

@app.get("/")
def root():
    return {"message": "Civic Educator API is running"}

port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

