"""
API routes for text generation and question answering.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from rag.pipeline import RAGPipeline
from models.embeddings import EmbeddingModel
from models.reranker import Reranker
from ingestion.index_builder import DocumentIndex

router = APIRouter()

# Request/Response Models
class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str
    top_k: int = 3
    max_length: int = 500
    temperature: float = 0.7

class Citation(BaseModel):
    """Citation model for sources."""
    source: str
    title: Optional[str] = None
    page: Optional[int] = None

class AnswerResponse(BaseModel):
    """Response model for answers."""
    answer: str
    citations: List[Citation]
    sources: List[str]
    context: List[str]

# Dependencies
def get_rag_pipeline() -> RAGPipeline:
    """Get the RAG pipeline instance."""
    if not hasattr(router, 'rag_pipeline') or not router.rag_pipeline:
        # Initialize components if not already done
        embedding_model = EmbeddingModel()
        reranker = Reranker()
        document_index = DocumentIndex()
        
        # In a real app, you would load the index here
        # document_index = DocumentIndex.load("path/to/index")
        
        router.rag_pipeline = RAGPipeline(
            index=document_index,
            embedding_model=embedding_model,
            reranker=reranker
        )
    return router.rag_pipeline

# Routes
@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Ask a question and get an answer using RAG.
    
    Args:
        request: Question request with parameters
        
    Returns:
        Generated answer with citations and sources
    """
    try:
        result = await rag_pipeline.query(
            question=request.question,
            top_k=request.top_k,
            max_length=request.max_length,
            temperature=request.temperature
        )
        
        # Format citations
        citations = [
            Citation(
                source=cit["source"],
                title=cit.get("title"),
                page=cit.get("page")
            )
            for cit in result["citations"]
        ]
        
        return {
            "answer": result["answer"],
            "citations": citations,
            "sources": result["sources"],
            "context": result["context"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )

@router.post("/generate")
async def generate_text(
    prompt: str,
    max_length: int = 200,
    temperature: float = 0.7,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Generate text based on a prompt (without retrieval).
    
    Args:
        prompt: The input prompt
        max_length: Maximum length of the generated text
        temperature: Sampling temperature
        
    Returns:
        Generated text
    """
    try:
        # In a real implementation, you would call an LLM here
        # For now, we'll return a simple response
        return {
            "generated_text": f"This is a placeholder response to the prompt: {prompt}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating text: {str(e)}"
        )
