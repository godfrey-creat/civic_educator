"""
API routes for document retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from rag.pipeline import RAGPipeline
from models.embeddings import EmbeddingModel
from models.reranker import Reranker
from ingestion.index_builder import DocumentIndex

router = APIRouter()

# Response Models
class SearchResult(BaseModel):
    """Search result model."""
    content: str
    score: float
    metadata: dict
    source: str

class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult]
    total: int

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
@router.get("/search", response_model=SearchResponse)
async def search_documents(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.5,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Search for documents relevant to the query.
    
    Args:
        query: The search query
        top_k: Maximum number of results to return
        score_threshold: Minimum relevance score (0-1)
        
    Returns:
        List of relevant documents with scores
    """
    try:
        results = await rag_pipeline.retrieve(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        return {
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )

@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get a specific document by ID.
    
    Args:
        doc_id: Document ID
        
    Returns:
        The requested document
    """
    try:
        # In a real implementation, you would fetch the document from storage
        # For now, we'll return a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document retrieval not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )

@router.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    List all available documents with pagination.
    
    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        
    Returns:
        Paginated list of documents
    """
    try:
        if not rag_pipeline.index:
            return {"documents": [], "total": 0}
            
        documents = rag_pipeline.index.documents[skip:skip + limit]
        return {
            "documents": documents,
            "total": len(rag_pipeline.index.documents),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )
