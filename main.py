from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uuid
from datetime import datetime
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure static and template directories
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# @app.get("/", response_class=HTMLResponse)
# async def read_index(request: Request):
#     return templates.TemplateResponse("CivicNavigatorMVP.html", {"request": request})

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Database Initialization
def init_db():
    conn = sqlite3.connect('civicnavigator.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS incidents
                 (id TEXT PRIMARY KEY, title TEXT, description TEXT, category TEXT, location TEXT, contact TEXT,
                  status TEXT, last_update TEXT, history TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kb_docs
                 (id TEXT PRIMARY KEY, title TEXT, body TEXT, tags TEXT, source TEXT, last_updated TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Pydantic Models
class ChatMessage(BaseModel):
    message: str
    role: str

class Incident(BaseModel):
    title: str
    description: str
    category: str
    location: str
    contact: str

class KbDoc(BaseModel):
    id: str
    title: str
    body: str
    tags: List[str]
    source: Optional[str]
    last_updated: str

# Mock KB
KB = [
    {"id": str(uuid.uuid4()), "title": "Garbage Collection Schedule", "body": "Garbage collection in South C occurs on Mondays and Thursdays. On public holidays, collection is rescheduled to the next working day.", "tags": ["waste", "schedule", "South C"], "source": "http://example.com/waste", "last_updated": "2025-08-01"},
    {"id": str(uuid.uuid4()), "title": "Streetlight Maintenance", "body": "Report broken streetlights to the municipal office. Repairs are typically completed within 3-5 business days.", "tags": ["streetlight", "maintenance"], "source": "http://example.com/streetlight", "last_updated": "2025-08-01"}
]

@app.get("/garbage-day")
def get_garbage_day():
    return {"message": "Garbage is collected every Monday and Thursday"}

# Index KB
def index_kb():
    conn = sqlite3.connect('civicnavigator.db')
    c = conn.cursor()
    for doc in KB:
        embedding = model.encode(doc['body']).tolist()
        c.execute('INSERT OR REPLACE INTO kb_docs (id, title, body, tags, source, last_updated) VALUES (?, ?, ?, ?, ?, ?)',
                  (doc['id'], doc['title'], doc['body'], json.dumps(doc['tags']), doc['source'], doc['last_updated']))
    conn.commit()
    conn.close()
    return {"indexed_docs": len(KB), "indexed_chunks": len(KB)}

index_kb()

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "all-MiniLM-L6-v2", "version": "1.0.0"}

# Chat Endpoint
@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        query_embedding = model.encode(message.message)
        conn = sqlite3.connect('civicnavigator.db')
        c = conn.cursor()
        c.execute('SELECT id, title, body, source FROM kb_docs')
        docs = c.fetchall()
        scores = []
        for doc in docs:
            doc_embedding = model.encode(doc[2])
            score = np.dot(query_embedding, doc_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding))
            scores.append((doc, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        top_doc = scores[0][0]
        response = {
            "reply": top_doc[2][:200],
            "citations": [{"title": top_doc[1], "snippet": top_doc[2][:100], "source_link": top_doc[3]}],
            "confidence": float(scores[0][1])
        }
        conn.close()
        logger.info(f"Chat query: {message.message}, response: {response['reply']}")
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing chat request")

# Incident Creation
@app.post("/incidents")
async def create_incident(incident: Incident):
    try:
        incident_id = str(uuid.uuid4())
        history = json.dumps([{"note": "Incident created", "timestamp": datetime.utcnow().isoformat()}])
        conn = sqlite3.connect('civicnavigator.db')
        c = conn.cursor()
        c.execute('INSERT INTO incidents (id, title, description, category, location, contact, status, last_update, history) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (incident_id, incident.title, incident.description, incident.category, incident.location, incident.contact, "NEW", datetime.utcnow().isoformat(), history))
        conn.commit()
        conn.close()
        logger.info(f"Incident created: {incident_id}")
        return {"incident_id": incident_id, "status": "NEW"}
    except Exception as e:
        logger.error(f"Incident creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating incident")

# Incident Status
@app.get("/incidents/{incident_id}")
async def get_incident_status(incident_id: str):
    try:
        conn = sqlite3.connect('civicnavigator.db')
        c = conn.cursor()
        c.execute('SELECT id, status, last_update, history FROM incidents WHERE id = ?', (incident_id,))
        incident = c.fetchone()
        conn.close()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return {
            "incident_id": incident[0],
            "status": incident[1],
            "last_update": incident[2],
            "history": json.loads(incident[3])
        }
    except Exception as e:
        logger.error(f"Incident status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching incident status")

# KB Search
@app.get("/kb/search")
async def search_kb():
    try:
        conn = sqlite3.connect('civicnavigator.db')
        c = conn.cursor()
        c.execute('SELECT id, title, body FROM kb_docs')
        docs = c.fetchall()
        conn.close()
        return [{"doc_id": doc[0], "title": doc[1], "snippet": doc[2][:100], "score": 1.0} for doc in docs]
    except Exception as e:
        logger.error(f"KB search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching knowledge base")

# Local Dev Entry Point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9756)
