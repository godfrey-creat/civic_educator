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
from config import settings
import os

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
        # Load or build index (shared logic)
        try:
            if (settings.INDEX_DIR / "index.faiss").exists():
                document_index = DocumentIndex.load(str(settings.INDEX_DIR))
            else:
                document_index = DocumentIndex(index_path=str(settings.INDEX_DIR))
                from ingestion.document_loader import DocumentLoader
                loader = DocumentLoader()
                for root, _, files in os.walk(settings.KNOWLEDGE_BASE_DIR):
                    for fname in files:
                        if fname.lower().endswith((".pdf", ".txt", ".md", ".docx")):
                            fpath = os.path.join(root, fname)
                            doc = loader.load_document(fpath)
                            document_index.add_document(doc["content"], doc["metadata"])
                document_index.build_index()
                document_index.save(str(settings.INDEX_DIR))
        except Exception:
            document_index = DocumentIndex()
        
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

@router.post("/reindex")
async def reindex_kb(rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)):
    """Rebuild the vector index from the knowledge base directory."""
    try:
        from ingestion.document_loader import DocumentLoader
        loader = DocumentLoader()
        new_index = DocumentIndex(index_path=str(settings.INDEX_DIR))
        indexed_docs = 0
        for root, _, files in os.walk(settings.KNOWLEDGE_BASE_DIR):
            for fname in files:
                if fname.lower().endswith((".pdf", ".txt", ".md", ".docx")):
                    fpath = os.path.join(root, fname)
                    doc = loader.load_document(fpath)
                    new_index.add_document(doc["content"], doc["metadata"])
                    indexed_docs += 1
        new_index.build_index()
        new_index.save(str(settings.INDEX_DIR))
        # Hot-swap into pipeline
        rag_pipeline.index = new_index
        return {"indexed_docs": indexed_docs, "indexed_chunks": len(new_index.chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing KB: {e}")

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
