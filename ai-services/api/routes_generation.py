"""
API routes for text generation and question answering.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
import os

from rag.pipeline import RAGPipeline
from models.embeddings import EmbeddingModel
from models.reranker import Reranker
from ingestion.index_builder import DocumentIndex
from models.generation.gemini_client import GeminiClient
from config import settings

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
    title: Optional[str] = None
    snippet: Optional[str] = None
    source_link: Optional[str] = None
    page: Optional[int] = None

class AnswerResponse(BaseModel):
    """Response model for answers."""
    answer: str
    citations: List[Citation]
    sources: List[str]

# Dependencies
def get_rag_pipeline() -> RAGPipeline:
    """Get the RAG pipeline instance."""
    if not hasattr(router, 'rag_pipeline') or not router.rag_pipeline:
        # Initialize components if not already done
        embedding_model = EmbeddingModel()
        reranker = Reranker()
        # Load or build index
        try:
            if (settings.INDEX_DIR / "index.faiss").exists():
                document_index = DocumentIndex.load(str(settings.INDEX_DIR))
            else:
                document_index = DocumentIndex(index_path=str(settings.INDEX_DIR))
                # Ingest PDFs from KB
                from ingestion.document_loader import DocumentLoader
                loader = DocumentLoader()
                # Walk the KB directory for files
                for root, _, files in os.walk(settings.KNOWLEDGE_BASE_DIR):
                    for fname in files:
                        if fname.lower().endswith((".pdf", ".txt", ".md", ".docx")):
                            fpath = os.path.join(root, fname)
                            doc = loader.load_document(fpath)
                            document_index.add_document(doc["content"], doc["metadata"])
                document_index.build_index()
                document_index.save(str(settings.INDEX_DIR))
        except Exception as e:
            # Fallback to empty index if load/build fails
            document_index = DocumentIndex()
        
        generator = GeminiClient(api_key=settings.GOOGLE_API_KEY)
        
        router.rag_pipeline = RAGPipeline(
            index=document_index,
            embedding_model=embedding_model,
            reranker=reranker,
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            max_retrieved_docs=settings.MAX_RETRIEVED_DOCS,
            generator=generator
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
        
        # Format citations (title, snippet, source_link, page)
        citations = [Citation(**{k: v for k, v in cit.items() if k in {"title", "snippet", "source_link", "page"}}) for cit in result.get("citations", [])]
        
        return {
            "answer": result.get("answer", ""),
            "citations": citations,
            "sources": result.get("sources", []),
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
