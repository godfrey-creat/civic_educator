"""
Text embedding models for document and query encoding.
"""
import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingModel:
    """Wrapper for text embedding models."""
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the pre-trained model to use
            device: Device to run the model on ('cuda', 'mps', 'cpu')
        """
        self.model_name = model_name or "all-MiniLM-L6-v2"
        self.device = device or self._get_default_device()
        self.model = self._load_model()
    
    def _get_default_device(self) -> str:
        """Get the default device for model inference."""
        import torch
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'
    
    def _load_model(self):
        """Load the pre-trained model."""
        logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
        try:
            return SentenceTransformer(self.model_name, device=self.device)
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            raise
    
    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text documents to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings (lists of floats)
        """
        if not texts:
            return []
            
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating document embeddings: {str(e)}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding as a list of floats
        """
        try:
            embedding = self.model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        # Use a dummy query to get the embedding dimension if not already known
        dummy_embedding = self.embed_query("dummy")
        return len(dummy_embedding)
