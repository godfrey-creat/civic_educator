"""
FastAPI application for the Civic Educator AI service.
"""
import logging
import os
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, Callable
import uvicorn

from config import settings
from rag.pipeline import RAGPipeline
from models.embeddings import EmbeddingModel
from models.reranker import Reranker
from ingestion.index_builder import DocumentIndex
from . import routes_chat, routes_health
from .schemas import ErrorResponse
from rag.pipeline import RAGPipeline
import sys
sys.path.append('/app')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Civic Educator AI Service",
    description="AI-powered question answering service for civic education",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Include routers
app.include_router(routes_chat.router)
app.include_router(routes_health.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions globally."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with detailed error messages."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            code="validation_error",
            details={"errors": exc.errors(), "body": exc.body}
        ).dict(),
    )

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="Not Found",
            code="not_found",
            details={"path": request.url.path}
        ).dict(),
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server Errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            code="internal_server_error",
            details={"message": str(exc) if settings.DEBUG else "An unexpected error occurred"}
        ).dict(),
    )

# Root endpoint with service information and links to docs
@app.get(
    "/",
    responses={
        200: {
            "description": "Basic service information",
            "content": {
                "application/json": {
                    "example": {
                        "service": "Civic Educator AI",
                        "status": "running",
                        "version": "0.1.0",
                        "docs": "/docs",
                        "health": "/health"
                    }
                }
            }
        }
    }
)
async def root() -> Dict[str, Any]:
    """
    Root endpoint with basic service information and links to documentation.
    
    Returns:
        Basic service information including status, version, and links to documentation.
    """
    return {
        "service": "Civic Educator AI",
        "status": "running",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            {"path": "/chat", "methods": ["POST"], "description": "Chat with the AI"},
            {"path": "/health", "methods": ["GET"], "description": "Service health check"},
            {"path": "/metrics", "methods": ["GET"], "description": "Service metrics (Prometheus format)"}
        ]
    }

# Add startup event to initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize the RAG pipeline
    try:
        # This will be cached by the dependency
        from .routes_chat import get_rag_pipeline
        pipeline = get_rag_pipeline()
        logger.info("RAG pipeline initialized successfully")
        
        return {
            "status": "healthy",
            "model": pipeline.embedding_model.model_name,
            "num_documents": len(pipeline.index.documents) if pipeline.index else 0,
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {e}", exc_info=True)
        raise

# Include routers
from .routes_retrieval import router as retrieval_router
from .routes_generation import router as generation_router

app.include_router(retrieval_router, prefix="/api/v1", tags=["retrieval"])
app.include_router(generation_router, prefix="/api/v1", tags=["generation"])

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1
    )
