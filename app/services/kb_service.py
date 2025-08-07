# app/services/kb_service.py
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import KnowledgeBaseDocument, KnowledgeBaseChunk
from app.schemas import KBSearchResult, KBDocument
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.chunk_size = 500  # Characters per chunk
        self.chunk_overlap = 50  # Overlap between chunks
    
    async def search(self, query: str, limit: int = 5, db: Session = None) -> List[Dict[str, Any]]:
        """Search knowledge base using embeddings and text matching"""
        try:
            results = []
            
            # Generate query embedding
            query_embeddings = await self.ai_service.generate_embeddings([query])
            query_embedding = query_embeddings[0]
            
            # Get all chunks for similarity search
            chunks = db.query(KnowledgeBaseChunk).join(KnowledgeBaseDocument).all()
            
            if not chunks:
                logger.warning("No knowledge base chunks found")
                return []
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                if chunk.embedding:
                    similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                    similarities.append((chunk, similarity))
            
            # Sort by similarity and get top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunks = similarities[:limit * 2]  # Get more for text filtering
            
            # Also do text-based search for keywords
            text_matches = self._text_search(query, db, limit)
            
            # Combine and deduplicate results
            seen_docs = set()
            for chunk, score in top_chunks:
                if chunk.document.id not in seen_docs:
                    results.append({
                        "doc_id": str(chunk.document.id),
                        "title": chunk.document.title,
                        "snippet": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        "content": chunk.content,
                        "score": float(score),
                        "source_url": chunk.document.source_url,
                        "tags": chunk.document.tags or []
                    })
                    seen_docs.add(chunk.document.id)
                
                if len(results) >= limit:
                    break
            
            # Add text matches that weren't already included
            for text_result in text_matches:
                if text_result["doc_id"] not in [r["doc_id"] for r in results]:
                    results.append(text_result)
                
                if len(results) >= limit:
                    break
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]):
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            
            a_np = np.array(a)
            b_np = np.array(b)
            
            dot_product = np.dot(a_np, b_np)
            norm_a = np.linalg.norm(a_np)
            norm_b = np.linalg.norm(b_np)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return float(dot_product / (norm_a * norm_b))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _text_search(self, query: str, db: Session, limit: int) -> List[Dict[str, Any]]:
        """Fallback text-based search"""
        try:
            query_words = query.lower().split()
            results = []
            
            documents = db.query(KnowledgeBaseDocument).all()
            
            for doc in documents:
                content_lower = (doc.title + " " + doc.content).lower()
                
                # Simple keyword matching
                matches = sum(1 for word in query_words if word in content_lower)
                if matches > 0:
                    score = matches / len(query_words)
                    results.append({
                        "doc_id": str(doc.id),
                        "title": doc.title,
                        "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        "content": doc.content,
                        "score": score,
                        "source_url": doc.source_url,
                        "tags": doc.tags or []
                    })
            
            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []
    
    async def create_or_update_document(
        self,
        title: str,
        content: str,
        tags: List[str] = None,
        source_url: str = None,
        db: Session = None
    ) -> KnowledgeBaseDocument:
        """Create or update a knowledge base document"""
        try:
            # Check if document exists
            existing_doc = db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.title == title
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.content = content
                existing_doc.tags = tags or []
                existing_doc.source_url = source_url
                existing_doc.updated_at = datetime.utcnow()
                existing_doc.indexed_at = None  # Mark for reindexing
                
                # Delete old chunks
                db.query(KnowledgeBaseChunk).filter(
                    KnowledgeBaseChunk.document_id == existing_doc.id
                ).delete()
                
                document = existing_doc
            else:
                # Create new document
                document = KnowledgeBaseDocument(
                    title=title,
                    content=content,
                    tags=tags or [],
                    source_url=source_url,
                    created_at=datetime.utcnow()
                )
                db.add(document)
                db.flush()  # Get the ID
            
            # Create chunks and embeddings
            await self._create_chunks_and_embeddings(document, db)
            
            db.commit()
            logger.info(f"Created/updated document: {title}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating/updating document: {e}")
            db.rollback()
            raise
    
    async def _create_chunks_and_embeddings(self, document: KnowledgeBaseDocument, db: Session):
        """Create chunks and generate embeddings for a document"""
        try:
            # Split content into chunks
            chunks = self._split_text(document.content)
            
            if not chunks:
                return
            
            # Generate embeddings for all chunks
            embeddings = await self.ai_service.generate_embeddings(chunks)
            
            # Create chunk records
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = KnowledgeBaseChunk(
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i,
                    embedding=embedding,
                    metadata={"length": len(chunk_text)},
                    created_at=datetime.utcnow()
                )
                db.add(chunk)
            
            # Update document indexed timestamp
            document.indexed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error creating chunks and embeddings: {e}")
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        
        # Simple sentence-aware chunking
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed chunk size
            if len(current_chunk + sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_words = current_chunk.split()[-10:]  # Take last 10 words
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def reindex(self, db: Session) -> Dict[str, Any]:
        """Reindex all documents in the knowledge base"""
        try:
            # Get all documents
            documents = db.query(KnowledgeBaseDocument).all()
            
            indexed_docs = 0
            indexed_chunks = 0
            
            for document in documents:
                # Delete existing chunks
                db.query(KnowledgeBaseChunk).filter(
                    KnowledgeBaseChunk.document_id == document.id
                ).delete()
                
                # Recreate chunks and embeddings
                await self._create_chunks_and_embeddings(document, db)
                
                # Count chunks for this document
                chunk_count = db.query(KnowledgeBaseChunk).filter(
                    KnowledgeBaseChunk.document_id == document.id
                ).count()
                
                indexed_chunks += chunk_count
                indexed_docs += 1
            db.commit()
            
            result = {
                "indexed_docs": indexed_docs,
                "indexed_chunks": indexed_chunks,
                "status": "completed",
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Reindexed {indexed_docs} documents, {indexed_chunks} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error reindexing knowledge base: {e}")
            db.rollback()
            return {
                "indexed_docs": 0,
                "indexed_chunks": 0,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def list_documents(
        self, 
        limit: int = 50, 
        offset: int = 0, 
        db: Session = None
    ) -> List[KBDocument]:
        """List knowledge base documents"""
        try:
            documents = db.query(KnowledgeBaseDocument).order_by(
                desc(KnowledgeBaseDocument.updated_at)
            ).offset(offset).limit(limit).all()
            
            return [
                KBDocument(
                    id=str(doc.id),
                    title=doc.title,
                    content=doc.content,
                    tags=doc.tags or [],
                    source_url=doc.source_url,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    indexed_at=doc.indexed_at
                )
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    async def delete_document(self, doc_id: str, db: Session) -> bool:
        """Delete a knowledge base document and its chunks"""
        try:
            document = db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.id == doc_id
            ).first()
            
            if not document:
                return False
            
            # Delete chunks (cascading should handle this, but explicit is better)
            db.query(KnowledgeBaseChunk).filter(
                KnowledgeBaseChunk.document_id == document.id
            ).delete()
            
            # Delete document
            db.delete(document)
            db.commit()
            
            logger.info(f"Deleted document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            db.rollback()
            return False


# app/services/notification_service.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from app.config import settings
from app.models import Incident

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, config):
        self.config = config
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load email templates"""
        return {
            "incident_created": """
Dear Resident,

Thank you for reporting an incident through CivicNavigator.

**Incident Details:**
- Reference ID: {incident_id}
- Title: {title}
- Category: {category}
- Status: {status}

Your report has been received and will be reviewed by our team. You can check the status anytime using your reference ID.

Best regards,
CivicNavigator Team
            """,
            
            "incident_updated": """
Dear Resident,

Your incident report has been updated.

**Incident Details:**
- Reference ID: {incident_id}
- Title: {title}
- Category: {category}
- Previous Status: {old_status}
- New Status: {new_status}

Thank you for using CivicNavigator.

Best regards,
CivicNavigator Team
            """,
            
            "staff_new_incident": """
New Incident Report

**Incident Details:**
- ID: {incident_id}
- Title: {title}
- Category: {category}
- Priority: {priority}
- Location: {location}
- Contact: {contact}

Please review and assign accordingly.

CivicNavigator System
            """
        }
    
    async def send_email(
        self,
        recipient: str,
        subject: str,
        template: str = None,
        content: str = None,
        variables: Dict[str, Any] = None
    ):
        """Send email notification"""
        try:
            if not settings.SMTP_HOST:
                logger.warning("SMTP not configured, skipping email notification")
                return
            
            # Prepare content
            if template and template in self.templates:
                email_content = self.templates[template].format(**(variables or {}))
            elif content:
                email_content = content
            else:
                email_content = "No content provided"
            
            # Create message
            message = MIMEMultipart()
            message["From"] = settings.FROM_EMAIL
            message["To"] = recipient
            message["Subject"] = subject
            
            message.attach(MIMEText(email_content, "plain"))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USERNAME:
                    server.starttls()
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                server.send_message(message)
            
            logger.info(f"Email sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {e}")
    
    async def send_sms(self, recipient: str, message: str):
        """Send SMS notification (placeholder - integrate with SMS service)"""
        try:
            # This would integrate with services like Twilio, Africa's Talking, etc.
            logger.info(f"SMS would be sent to {recipient}: {message[:50]}...")
            
            # For demo purposes, we'll just log
            # In production, implement actual SMS sending
            
        except Exception as e:
            logger.error(f"Error sending SMS to {recipient}: {e}")
    
    async def notify_staff_new_incident(self, incident: Incident):
        """Notify staff about new incident"""
        try:
            # This could send to a staff email list, Slack webhook, etc.
            content = self.templates["staff_new_incident"].format(
                incident_id=incident.id,
                title=incident.title,
                category=incident.category.replace('_', ' ').title(),
                priority=incident.priority,
                location=incident.location_text or "Not provided",
                contact=incident.contact_email or incident.contact_phone or "Not provided"
            )
            
            # For demo, just log
            logger.info(f"Staff notification for incident {incident.id}: {content[:100]}...")
            
            # In production, send to staff channels
            
        except Exception as e:
            logger.error(f"Error notifying staff about incident {incident.id}: {e}")
    
    async def notify_incident_escalation(self, incident: Incident, escalation_reason: str):
        """Notify management about incident escalation"""
        try:
            subject = f"Incident Escalation - {incident.id}"
            content = f"""
INCIDENT ESCALATION ALERT

Incident {incident.id} requires management attention.

Details:
- Title: {incident.title}
- Category: {incident.category}
- Priority: {incident.priority}
- Age: {(incident.updated_at - incident.created_at).days} days
- Escalation Reason: {escalation_reason}

Please review immediately.
"""
            
            # Log escalation (in production, send to management)
            logger.warning(f"Escalation for {incident.id}: {escalation_reason}")
            
        except Exception as e:
            logger.error(f"Error sending escalation notification: {e}")