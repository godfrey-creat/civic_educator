"""
Reranking models to improve search result quality.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class Reranker:
    """
    Reranks search results using a cross-encoder model.
    This helps improve the quality of search results by considering query-document interactions.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = None):
        """
        Initialize the reranker.
        
        Args:
            model_name: Name of the cross-encoder model to use
            device: Device to run the model on ('cuda', 'mps', 'cpu')
        """
        self.model_name = model_name
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
        """Load the cross-encoder model."""
        logger.info(f"Loading reranker model: {self.model_name} on {self.device}")
        try:
            return CrossEncoder(
                self.model_name,
                device=self.device,
                max_length=512,
                automodel_args={'local_files_only': False}
            )
        except Exception as e:
            logger.error(f"Failed to load reranker model {self.model_name}: {str(e)}")
            raise
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on their relevance to the query.
        
        Args:
            query: The search query
            documents: List of document dictionaries with 'content' and 'metadata' keys
            top_k: Number of top documents to return
            score_threshold: Minimum score threshold for including results
            
        Returns:
            List of reranked documents with updated scores
        """
        if not documents:
            return []
        
        try:
            # Prepare pairs for the cross-encoder
            pairs = [[query, doc['content']] for doc in documents]
            
            # Get scores from the cross-encoder
            scores = self.model.predict(
                pairs,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Update documents with new scores
            for doc, score in zip(documents, scores):
                doc['score'] = float(score)
            
            # Sort by score in descending order
            reranked = sorted(documents, key=lambda x: x['score'], reverse=True)
            
            # Apply threshold and limit to top_k
            filtered = [doc for doc in reranked if doc['score'] >= score_threshold][:top_k]
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            # Return original documents if reranking fails
            return documents[:top_k]
    
    def rerank_with_hybrid_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        alpha: float = 0.5,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using a combination of first-stage and cross-encoder scores.
        
        Args:
            query: The search query
            documents: List of document dictionaries with 'content', 'score', and 'metadata' keys
            alpha: Weight for the first-stage score (1.0 = use only first-stage, 0.0 = use only cross-encoder)
            top_k: Number of top documents to return
            score_threshold: Minimum score threshold for including results
            
        Returns:
            List of reranked documents with updated scores
        """
        if not documents:
            return []
        
        try:
            # Get cross-encoder scores
            pairs = [[query, doc['content']] for doc in documents]
            cross_scores = self.model.predict(
                pairs,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Normalize both scores to [0, 1] range
            first_stage_scores = np.array([doc.get('score', 0.0) for doc in documents])
            first_stage_scores = (first_stage_scores - first_stage_scores.min()) / \
                               (first_stage_scores.max() - first_stage_scores.min() + 1e-9)
            
            cross_scores = (cross_scores - cross_scores.min()) / \
                          (cross_scores.max() - cross_scores.min() + 1e-9)
            
            # Combine scores
            combined_scores = alpha * first_stage_scores + (1 - alpha) * cross_scores
            
            # Update documents with combined scores
            for doc, score in zip(documents, combined_scores):
                doc['score'] = float(score)
            
            # Sort by combined score in descending order
            reranked = sorted(documents, key=lambda x: x['score'], reverse=True)
            
            # Apply threshold and limit to top_k
            filtered = [doc for doc in reranked if doc['score'] >= score_threshold][:top_k]
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error during hybrid reranking: {str(e)}")
            # Return original documents if reranking fails
            return documents[:top_k]
