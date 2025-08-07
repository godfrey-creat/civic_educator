# app/services/chat_service.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Conversation, Message, MessageSender
from app.schemas import ChatResponse, ChatMessage, UserContext
from app.services.ai_service import AIService
from app.services.kb_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        
    async def process_message(
        self, 
        session_id: str, 
        message: str, 
        user_context: Optional[UserContext] = None,
        db: Session = None
    ) -> ChatResponse:
        """Process a chat message and generate response"""
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(session_id, user_context, db)
            
            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                sender=MessageSender.USER,
                content=message,
                created_at=datetime.utcnow()
            )
            db.add(user_message)
            db.flush()  # Get the ID
            
            # Classify intent
            intent, intent_confidence = await self.ai_service.classify_intent(message)
            logger.info(f"Classified intent: {intent} (confidence: {intent_confidence:.2f})")
            
            # Handle different intents
            if intent == "incident_report":
                response_data = await self._handle_incident_guidance(message, user_context)
            elif intent == "status_check":
                response_data = await self._handle_status_check_guidance(message)
            elif intent == "greeting":
                response_data = await self._handle_greeting(message, user_context)
            else:  # service_question or out_of_scope
                response_data = await self._handle_service_question(message, user_context, conversation, db)
            
            # Create assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                sender=MessageSender.ASSISTANT,
                content=response_data["response"],
                citations=response_data.get("citations", []),
                confidence=response_data.get("confidence", 0.5),
                metadata={"intent": intent, "intent_confidence": intent_confidence},
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            db.commit()
            
            return ChatResponse(
                reply=response_data["response"],
                citations=response_data.get("citations", []),
                confidence=response_data.get("confidence", 0.5),
                steps=response_data.get("steps"),
                session_id=session_id,
                requires_clarification=response_data.get("requires_clarification", False),
                clarification_question=response_data.get("clarification_question")
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            db.rollback()
            return ChatResponse(
                reply="I apologize, but I'm having trouble processing your message right now. Please try again.",
                citations=[],
                confidence=0.0,
                session_id=session_id
            )
    
    def _get_or_create_conversation(
        self, 
        session_id: str, 
        user_context: Optional[UserContext],
        db: Session
    ) -> Conversation:
        """Get existing conversation or create new one"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                user_context=user_context.dict() if user_context else None,
                created_at=datetime.utcnow()
            )
            db.add(conversation)
            db.flush()
        elif user_context:
            # Update user context if provided
            conversation.user_context = user_context.dict()
            conversation.updated_at = datetime.utcnow()
        
        return conversation
    
    async def _handle_incident_guidance(
        self, 
        message: str, 
        user_context: Optional[UserContext]
    ) -> Dict[str, Any]:
        """Handle incident reporting guidance"""
        response = """I can help you report an incident! To file a report, I'll need some information:

📝 **What you'll need:**
- Brief title describing the issue
- Detailed description of the problem
- Category (road maintenance, waste management, water supply, electricity, street lighting, drainage, or other)
- Location (address or landmark)
- Your contact information (email or phone)
- Optional: Photo of the issue

Would you like to start filing an incident report now, or do you have questions about the reporting process?"""

        return {
            "response": response,
            "citations": [],
            "confidence": 0.9,
            "requires_clarification": True,
            "clarification_question": "Would you like to file an incident report or learn more about the process?"
        }
    
    async def _handle_status_check_guidance(self, message: str) -> Dict[str, Any]:
        """Handle status check guidance"""
        response = """I can help you check the status of your incident report! 

🔍 **To check your report status:**
- You'll need your incident reference ID (format: INC-YYYY-###)
- This ID was provided when you submitted your report

Do you have your incident reference ID? If so, please share it and I'll look up the current status for you.

If you can't find your reference ID, please check:
- Your email confirmation
- SMS confirmation (if you provided a phone number)
- Any previous chat history where you filed the report"""

        return {
            "response": response,
            "citations": [],
            "confidence": 0.9,
            "requires_clarification": True,
            "clarification_question": "Do you have your incident reference ID to check the status?"
        }
    
    async def _handle_greeting(
        self, 
        message: str, 
        user_context: Optional[UserContext]
    ) -> Dict[str, Any]:
        """Handle greeting messages"""
        return await self.ai_service._handle_greeting(message, user_context.dict() if user_context else None)
    
    async def _handle_service_question(
        self, 
        message: str, 
        user_context: Optional[UserContext],
        conversation: Conversation,
        db: Session
    ) -> Dict[str, Any]:
        """Handle service-related questions using RAG"""
        try:
            # Search knowledge base
            from app.services.kb_service import KnowledgeBaseService
            kb_service = KnowledgeBaseService(self.ai_service)
            search_results = await kb_service.search(message, limit=5, db=db)
            
            # Get conversation history
            history = self._get_conversation_history(conversation, db)
            
            # Generate response using RAG
            response_data = await self.ai_service.generate_response(
                query=message,
                context=search_results,
                user_context=user_context.dict() if user_context else None,
                conversation_history=history
            )
            
            # Check if we need clarification for location-specific questions
            if self._needs_location_clarification(message, user_context, response_data):
                clarification = self._generate_location_clarification(message, user_context)
                response_data.update(clarification)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error handling service question: {e}")
            return {
                "response": "I apologize, but I'm having trouble accessing the knowledge base right now. Please try again or contact support.",
                "citations": [],
                "confidence": 0.0
            }
    
    def _get_conversation_history(self, conversation: Conversation, db: Session) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(desc(Message.created_at)).limit(10).all()
        
        history = []
        for msg in reversed(recent_messages):  # Reverse to get chronological order
            role = "user" if msg.sender == MessageSender.USER else "assistant"
            history.append({
                "role": role,
                "content": msg.content
            })
        
        return history
    
    def _needs_location_clarification(
        self, 
        message: str, 
        user_context: Optional[UserContext],
        response_data: Dict[str, Any]
    ) -> bool:
        """Check if we need to ask for location clarification"""
        if user_context and user_context.location:
            return False  # Already have location
        
        # Check if question is location-specific
        location_keywords = ["collection", "schedule", "my area", "here", "nearby", "local"]
        message_lower = message.lower()
        
        has_location_keyword = any(keyword in message_lower for keyword in location_keywords)
        low_confidence = response_data.get("confidence", 1.0) < 0.7
        
        return has_location_keyword and low_confidence
    
    def _generate_location_clarification(
        self, 
        message: str, 
        user_context: Optional[UserContext]
    ) -> Dict[str, str]:
        """Generate location clarification question"""
        return {
            "requires_clarification": True,
            "clarification_question": "To give you the most accurate information about services in your area, could you please tell me your location or ward? For example: 'Westlands', 'Karen', 'South C', etc."
        }
    
    async def get_history(self, session_id: str, db: Session) -> List[ChatMessage]:
        """Get chat history for a session"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            return []
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).all()
        
        return [
            ChatMessage(
                id=str(msg.id),
                sender=msg.sender,
                content=msg.content,
                citations=msg.citations or [],
                confidence=msg.confidence,
                created_at=msg.created_at
            )
            for msg in messages
        ]
    
    async def delete_history(self, session_id: str, db: Session):
        """Delete chat history for privacy"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if conversation:
            # Delete all messages first (due to foreign key constraint)
            db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).delete()
            
            # Delete conversation
            db.delete(conversation)
            db.commit()
            
            logger.info(f"Deleted chat history for session {session_id}")
    
    async def get_conversation_stats(self, db: Session) -> Dict[str, Any]:
        """Get conversation statistics for monitoring"""
        total_conversations = db.query(Conversation).count()
        total_messages = db.query(Message).count()
        
        # Recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_conversations = db.query(Conversation).filter(
            Conversation.created_at >= yesterday
        ).count()
        
        recent_messages = db.query(Message).filter(
            Message.created_at >= yesterday
        ).count()
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "recent_conversations_24h": recent_conversations,
            "recent_messages_24h": recent_messages,
            "avg_messages_per_conversation": total_messages / max(total_conversations, 1)
        }