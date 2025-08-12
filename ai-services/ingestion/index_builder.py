"""
Index building and management for document retrieval.
"""
import os
import json
import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import pickle

from .chunker import TextChunk, SemanticChunker, default_chunker
from .document_loader import DocumentLoader
from models.embeddings import EmbeddingModel
from config import settings

logger = logging.getLogger(__name__)

class DocumentIndex:
    """
    Manages document indexing and retrieval using FAISS for vector search.
    """
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize the document index.
        
        Args:
            index_path: Path to save/load the index
        """
        self.index_path = Path(index_path) if index_path else settings.INDEX_DIR / "faiss_index"
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize FAISS index
        self.index = None
        self.embedding_model = EmbeddingModel()
        self.chunker = default_chunker
        
        # Track documents and chunks
        self.documents = []  # List of document metadata
        self.chunks = []     # List of TextChunk objects
        self.chunk_to_doc = []  # Maps chunk index to document index
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> int:
        """
        Add a document to the index.
        
        Args:
            content: Document text content
            metadata: Document metadata
            
        Returns:
            Document ID
        """
        doc_id = len(self.documents)
        self.documents.append(metadata)
        
        # Chunk the document
        chunks = self.chunker.chunk_document(content, metadata)
        
        # Add chunks to index
        for chunk in chunks:
            self.chunks.append(chunk)
            self.chunk_to_doc.append(doc_id)
        
        return doc_id
    
    async def add_document_from_file(self, file_path: Union[str, Path]) -> int:
        """
        Load and index a document from a file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document ID
        """
        loader = DocumentLoader()
        doc = loader.load_document(file_path)
        return self.add_document(doc["content"], doc["metadata"])
    
    async def add_document_from_url(self, url: str) -> int:
        """
        Load and index a document from a URL.
        
        Args:
            url: URL of the document
            
        Returns:
            Document ID
        """
        loader = DocumentLoader()
        doc = await loader.load_from_url(url)
        return self.add_document(doc["content"], doc["metadata"])
    
    def build_index(self):
        """Build the FAISS index from all chunks."""
        if not self.chunks:
            logger.warning("No chunks to index")
            return
        
        # Generate embeddings for all chunks
        texts = [chunk.text for chunk in self.chunks]
        embeddings = self.embedding_model.embed_documents(texts)
        
        # Initialize FAISS index if not already done
        if self.index is None:
            dim = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dim)
        
        # Add vectors to the index
        self.index.add(np.array(embeddings).astype('float32'))
        logger.info(f"Built index with {len(embeddings)} vectors")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for relevant chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results with scores and metadata
        """
        if self.index is None or not self.chunks:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_vector, k)
        
        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0:  # Skip invalid indices
                continue
                
            chunk = self.chunks[idx]
            doc = self.documents[self.chunk_to_doc[idx]]
            
            results.append({
                'score': float(dist),
                'content': chunk.text,
                'metadata': chunk.metadata,
                'document': doc
            })
        
        return results
    
    def save(self, path: Optional[str] = None):
        """Save the index and metadata to disk."""
        save_path = Path(path) if path else self.index_path
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, str(save_path / "index.faiss"))
        
        # Save metadata
        with open(save_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump({
                'documents': self.documents,
                'chunks': [chunk.to_dict() for chunk in self.chunks],
                'chunk_to_doc': self.chunk_to_doc
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved index to {save_path}")
    
    @classmethod
    def load(cls, path: str) -> 'DocumentIndex':
        """Load a saved index from disk."""
        path = Path(path)
        index = cls(index_path=path)
        
        # Load FAISS index
        if (path / "index.faiss").exists():
            index.index = faiss.read_index(str(path / "index.faiss"))
        
        # Load metadata
        if (path / "metadata.json").exists():
            with open(path / "metadata.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                index.documents = data.get('documents', [])
                index.chunks = [TextChunk(**chunk) for chunk in data.get('chunks', [])]
                index.chunk_to_doc = data.get('chunk_to_doc', [])
        
        logger.info(f"Loaded index from {path} with {len(index.documents)} documents")
        return index

# Default index instance
default_index = DocumentIndex()
