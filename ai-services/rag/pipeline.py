"""
RAG (Retrieval-Augmented Generation) pipeline for question answering.

Features:
- Document retrieval with semantic search
- Confidence scoring for responses
- Clarification questions for low confidence
- Citation extraction and formatting
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import json
import numpy as np
from datetime import datetime

from models.embeddings import EmbeddingModel
from models.reranker import Reranker
from ingestion.index_builder import DocumentIndex
from config import settings

logger = logging.getLogger(__name__)

class RAGResponse:
    """Container for RAG pipeline response."""
    
    def __init__(
        self,
        answer: str,
        citations: List[Dict[str, Any]],
        confidence: float,
        needs_clarification: bool = False,
        clarification_question: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.answer = answer
        self.citations = citations
        self.confidence = confidence
        self.needs_clarification = needs_clarification
        self.clarification_question = clarification_question
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "answer": self.answer,
            "citations": self.citations,
            "confidence": float(self.confidence),
            "needs_clarification": self.needs_clarification,
            "clarification_question": self.clarification_question,
            "context": self.context
        }

class RAGPipeline:
    """End-to-end RAG pipeline for question answering."""
    
    def __init__(
        self,
        index: DocumentIndex,
        embedding_model: Optional[EmbeddingModel] = None,
        reranker: Optional[Reranker] = None,
        confidence_threshold: float = 0.7,
        max_retrieved_docs: int = 5,
    ):
        """Initialize the RAG pipeline.
        
        Args:
            index: Document index for retrieval
            embedding_model: Model for text embeddings (default: all-MiniLM-L6-v2)
            reranker: Optional reranker for improving retrieval quality
            confidence_threshold: Minimum confidence score (0-1) for high-confidence answers
            max_retrieved_docs: Maximum number of documents to retrieve
        """
        self.index = index
        self.embedding_model = embedding_model or EmbeddingModel()
        self.reranker = reranker or Reranker()
        self.confidence_threshold = confidence_threshold
        self.max_retrieved_docs = max_retrieved_docs
        
        logger.info("RAG pipeline initialized with confidence threshold: %.2f", 
                   self.confidence_threshold)

    async def _get_relevant_documents(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            top_k: Maximum number of documents to retrieve
            score_threshold: Minimum relevance score (0-1)
            
        Returns:
            List of relevant documents with scores and metadata
        """
        try:
            # Get query embedding
            query_embedding = self.embedding_model.embed_queries([query])[0]
            
            # Search the index
            results = self.index.search(query_embedding, top_k=top_k)
            
            # Filter by score threshold
            relevant_docs = [
                {
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": float(score),
                    "source": doc.get("source", "unknown"),
                    "title": doc.get("title", ""),
                }
                for doc, score in zip(results["documents"], results["scores"])
                if score >= score_threshold
            ]
            
            # Rerank if enabled
            if self.reranker and relevant_docs:
                return self._rerank_documents(query, relevant_docs)
                
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank documents using cross-encoder."""
        try:
            # Prepare query-document pairs for reranking
            pairs = [(query, doc["content"]) for doc in documents]
            
            # Get reranker scores
            scores = self.reranker.predict(pairs)
            
            # Update document scores and sort
            for doc, score in zip(documents, scores):
                doc["score"] = float(score)
                
            return sorted(documents, key=lambda x: x["score"], reverse=True)
            
        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return documents
    
    def _calculate_confidence(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        response: str
    ) -> float:
        """Calculate confidence score for the response."""
        if not documents:
            return 0.0
            
        # Simple confidence based on top document score
        top_score = documents[0]["score"]
        
        # Normalize score to 0-1 range (assuming scores are typically 0.5-1.0)
        confidence = min(1.0, max(0.0, (top_score - 0.5) * 2))
        
        # Additional confidence factors could be added here:
        # - Response length
        # - Presence of key terms from query
        # - Semantic similarity between query and response
        
        return confidence
    
    def _needs_clarification(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        confidence: float
    ) -> Tuple[bool, str]:
        """Determine if clarification is needed for the query."""
        if confidence < self.confidence_threshold / 2:
            return True, "I'm not entirely sure what you're asking. Could you provide more details?"
            
        # Check for ambiguous queries
        if len(documents) > 1 and documents[0]["score"] - documents[1]["score"] < 0.1:
            # Multiple documents with similar scores - ask for clarification
            topics = list(set(doc["metadata"].get("topic", "") for doc in documents[:3] if doc["metadata"].get("topic")))
            if topics:
                return True, f"I found information on multiple topics. Are you asking about {', '.join(topics[:2])}, or something else?"
        
        return False, ""
    
    def _format_citations(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format document chunks into citation format."""
        citations = []
        seen_sources = set()
        
        for doc in documents[:3]:  # Limit to top 3 citations
            source = doc.get("source", "")
            if not source or source in seen_sources:
                continue
                
            citations.append({
                "title": doc.get("title", ""),
                "snippet": doc["content"][:200] + "...",  # First 200 chars
                "source_link": source,
                "page": doc.get("metadata", {}).get("page")
            })
            seen_sources.add(source)
            
        return citations
    
    async def query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RAGResponse:
        """Process a user query and generate a response with citations.
        
        Args:
            query: User's question or input
            context: Optional conversation context
            **kwargs: Additional parameters for retrieval/generation
            
        Returns:
            RAGResponse with answer, citations, and metadata
        """
        try:
            # 1. Retrieve relevant documents
            documents = await self._get_relevant_documents(
                query,
                top_k=kwargs.get('top_k', self.max_retrieved_docs),
                score_threshold=kwargs.get('score_threshold', 0.5)
            )
            
            # 2. Generate response (placeholder - would use an LLM in production)
            # In a real implementation, this would call an LLM with the documents as context
            response_text = self._generate_response(query, documents, context)
            
            # 3. Calculate confidence
            confidence = self._calculate_confidence(query, documents, response_text)
            
            # 4. Check if clarification is needed
            needs_clarification, clarification_question = self._needs_clarification(
                query, documents, confidence
            )
            
            # 5. Format citations
            citations = self._format_citations(documents)
            
            # 6. Update conversation context if provided
            if context is not None:
                context.update({
                    "last_query": query,
                    "last_documents": [doc["source"] for doc in documents],
                    "last_confidence": confidence,
                })
            
            return RAGResponse(
                answer=response_text,
                citations=citations,
                confidence=confidence,
                needs_clarification=needs_clarification,
                clarification_question=clarification_question,
                context=context or {}
            )
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return RAGResponse(
                answer="I'm sorry, I encountered an error processing your request.",
                citations=[],
                confidence=0.0,
                context=context or {}
            )
    
    def _generate_response(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response based on the query and documents.
        
        In a real implementation, this would call an LLM with the documents as context.
        This is a simplified version that just returns the top document's content.
        """
        if not documents:
            return "I couldn't find any relevant information to answer your question."
            
        # In a real implementation, you would:
        # 1. Format the documents into a prompt
        # 2. Call an LLM with the prompt
        # 3. Return the generated response
        
        # For now, just return the top document's content
        top_doc = documents[0]
        return (
            f"Based on {top_doc.get('title', 'the document')}, "
            f"here's what I found: {top_doc['content'][:500]}..."
            "\n"
#Note: This is a placeholder response. In a real implementation, this would be generated by an LLM."
        )
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_reranker: bool = True,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            use_reranker: Whether to use the reranker
            score_threshold: Minimum score threshold for results
            
        Returns:
            List of relevant documents with scores and metadata
        """
        # First-stage retrieval using vector similarity
        results = self.index.search(query, top_k=top_k * 2)  # Get more results for reranking
        
        if not results:
            return []
        
        # Apply reranker if enabled
        if use_reranker and self.reranker and len(results) > 1:
            results = self.reranker.rerank_with_hybrid_scores(
                query=query,
                documents=results,
                alpha=0.5,  # Equal weight to both stages
                top_k=top_k,
                score_threshold=score_threshold
            )
        
        # Format results
        formatted_results = []
        for result in results[:top_k]:
            formatted_results.append({
                'content': result['content'],
                'score': result['score'],
                'metadata': result['metadata'],
                'source': result['metadata'].get('source', 'unknown')
            })
        
        return formatted_results
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        max_length: int = 500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a response to a query using the provided context.
        
        Args:
            query: The user's question
            context: List of relevant document chunks
            max_length: Maximum length of the generated response
            temperature: Sampling temperature for generation
            
        Returns:
            Dictionary containing the generated answer and citations
        """
        # Format the prompt with context and query
        prompt = self._format_prompt(query, context)
        
        try:
            # In a real implementation, this would call an LLM API or local model
            # For now, we'll return a simple response
            answer = self._generate_simple_response(query, context)
            
            # Extract citations from the context
            citations = self._extract_citations(context)
            
            return {
                'answer': answer,
                'citations': citations,
                'context': [c['content'] for c in context],
                'sources': list(set(c['source'] for c in context))
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'answer': "I'm sorry, I couldn't generate a response at the moment.",
                'citations': [],
                'context': [],
                'sources': []
            }
    
    def _format_prompt(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Format the prompt for the language model."""
        # Start with instructions
        prompt = [
            "You are a helpful assistant for Kenyan government services. "
            "Answer the question based on the provided context. "
            "If you don't know the answer, say you don't know.\n\n"
            "Context:"
        ]
        
        # Add context
        for i, doc in enumerate(context, 1):
            prompt.append(f"\n--- Document {i} ---\n{doc['content']}")
        
        # Add the query
        prompt.append(f"\n\nQuestion: {query}\nAnswer:")
        
        return "\n".join(prompt)
    
    def _generate_simple_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate a simple response for demo purposes."""
        if not context:
            return "I couldn't find any relevant information to answer your question."
            
        # This is a placeholder - in a real implementation, you would use an LLM
        return (
            f"Based on the available information, here's what I found regarding your question about '{query}'. "
            f"The relevant documents suggest the following: {context[0]['content'][:200]}... "
            "Please check the citations for more detailed information."
        )
    
    def _extract_citations(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citation information from context."""
        citations = []
        seen_sources = set()
        
        for doc in context:
            source = doc.get('metadata', {}).get('source')
            if not source or source in seen_sources:
                continue
                
            citations.append({
                'source': source,
                'title': doc.get('metadata', {}).get('title', 'Document'),
                'page': doc.get('metadata', {}).get('page')
            })
            seen_sources.add(source)
            
        return citations
    
    async def query(
        self,
        question: str,
        top_k: int = 3,
        max_length: int = 500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        End-to-end query processing: retrieve and generate.
        
        Args:
            question: The user's question
            top_k: Number of documents to retrieve
            max_length: Maximum length of the generated response
            temperature: Sampling temperature for generation
            
        Returns:
            Dictionary containing the answer and supporting information
        """
        # Retrieve relevant context
        context = await self.retrieve(question, top_k=top_k)
        
        # Generate response
        response = await self.generate_response(
            query=question,
            context=context,
            max_length=max_length,
            temperature=temperature
        )
        
        return response
