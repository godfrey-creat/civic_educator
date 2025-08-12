"""
Chat API endpoints for the Civic Educator AI service.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from rag.pipeline import RAGPipeline
from .schemas import ChatRequest, ChatResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory conversation store (in a real app, use a database)
conversation_store: Dict[str, Dict[str, Any]] = {}

def get_rag_pipeline() -> RAGPipeline:
    """Get or initialize the RAG pipeline."""
    if not hasattr(get_rag_pipeline, "pipeline"):
        from rag.pipeline import RAGPipeline
        from models.embeddings import EmbeddingModel
        from models.reranker import Reranker
        from ingestion.index_builder import DocumentIndex
        
        # Initialize components
        embedding_model = EmbeddingModel()
        reranker = Reranker()
        document_index = DocumentIndex()  # This would load your index
        
        # Create pipeline
        get_rag_pipeline.pipeline = RAGPipeline(
            index=document_index,
            embedding_model=embedding_model,
            reranker=reranker,
            confidence_threshold=0.7
        )
    return get_rag_pipeline.pipeline

@router.post(
    "", 
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def chat_endpoint(
    request: ChatRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
) -> ChatResponse:
    """
    Handle a chat message and return a response with citations.
    
    This endpoint processes natural language questions and returns answers with
    citations from the knowledge base.
    """
    try:
        # Get or create conversation context
        conversation_id = request.conversation_id or "default"
        context = conversation_store.get(conversation_id, {})
        
        # Process the query with the correct parameters
        response = await rag_pipeline.query(
            question=request.message,
            top_k=request.context.get('top_k', 3) if request.context else 3,
            max_length=request.context.get('max_length', 500) if request.context else 500,
            temperature=request.context.get('temperature', 0.7) if request.context else 0.7
        )
        
        # Update conversation store
        conversation_store[conversation_id] = response.context
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "code": "internal_server_error",
                "details": str(e)
            }
        )

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history (placeholder implementation)."""
    if conversation_id not in conversation_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Conversation not found", "code": "not_found"}
        )
    return {"conversation_id": conversation_id, "context": conversation_store[conversation_id]}

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in conversation_store:
        del conversation_store[conversation_id]
    return None
