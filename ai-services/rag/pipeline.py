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
from datetime import datetime, timezone, timedelta
from pathlib import Path

from models.embeddings import EmbeddingModel
from models.reranker import Reranker
from models.generation.gemini_client import GeminiClient
from ingestion.index_builder import DocumentIndex
from config import settings
from utils.web_search import SerpAPIClient
from utils.text import slugify, now_iso

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
        generator: Optional[GeminiClient] = None,
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
        self.generator = generator
        self.search_client = SerpAPIClient(api_key=settings.SERPAPI_KEY)
        
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
            # Search the index directly with raw query; underlying index handles embedding
            results = self.index.search(query, k=top_k)
            
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
        question: str,
        top_k: int = 3,
        max_length: int = 500,
        temperature: float = 0.7,
        **kwargs
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
        
        # Generate grounded response
        response = await self.generate_response(
            query=question,
            context=context,
            max_length=max_length,
            temperature=temperature
        )
        
        # Confidence gating and fallback
        try:
            confidence = self._calculate_confidence(question, context, response.get('answer', ''))
        except Exception:
            confidence = 0.0
        
        if (not context or confidence < self.confidence_threshold) and self.generator and self.generator.available():
            # Attempt cached freshness check is implicit via RAG; proceed to live web search
            web = None
            try:
                web = self.search_client.search(question) if self.search_client.available() else None
            except Exception as e:
                logger.warning("Web search failed: %s", e)

            if web and web.get('link'):
                # Summarize using Gemini if possible; otherwise use snippet
                summary_prompt = (
                    "You are a helpful civic information assistant. Based on the following search snippet, "
                    "provide a concise, actionable answer for a Nairobi resident. If schedules vary by ward, say so and advise checking the link.\n\n"
                    f"Snippet: {web.get('snippet','')}\n\n"
                    "Respond in 1-3 sentences."
                )
                answer_text = self.generator.generate(summary_prompt)
                if not answer_text.strip():
                    answer_text = web.get('snippet') or "I'm sorry, I couldn't find a definitive answer right now."

                # Persist to answers dir and index incrementally
                try:
                    date_fetched = now_iso()
                    filename = slugify(question) + ".md"
                    out_path = Path(settings.ANSWERS_DIR) / filename
                    md = (
                        f"# {question}\n\n" 
                        f"{answer_text}\n\n"
                        f"Source: {web.get('link')}\n\n"
                        f"Date fetched: {date_fetched}\n"
                    )
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(md, encoding='utf-8')

                    # Index immediately with metadata
                    metadata = {
                        'source': web.get('link'),
                        'type': 'web_answer',
                        'question': question,
                        'date_fetched': date_fetched,
                        'title': web.get('title', ''),
                    }
                    self.index.add_document_and_index(content=md, metadata=metadata)
                    self.index.save(str(settings.INDEX_DIR))
                except Exception as e:
                    logger.warning("Failed to persist/index web answer: %s", e)

                return {
                    'answer': answer_text,
                    'citations': [{'title': web.get('title',''), 'snippet': web.get('snippet',''), 'source_link': web.get('link')}],
                    'context': [],
                    'sources': ['web']
                }
            else:
                # No web results; at least return LLM fallback
                fallback_answer = self.generator.generate(question)
                return {
                    'answer': fallback_answer,
                    'citations': [],
                    'context': [],
                    'sources': ['gemini']
                }
        
        return response
    
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
        # First-stage retrieval using vector similarity (get more for reranking)
        results = self.index.search(query, k=top_k * 2)
        
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
        # Limit and clean context for synthesis
        top_context = context[:3] if context else []
        prompt = self._format_prompt(query, top_context)
        
        try:
            # Prefer LLM synthesis if available to keep responses concise
            if self.generator and self.generator.available():
                synthesis_prompt = (
                    "You are a helpful civic information assistant for Nairobi.\n"
                    "Based ONLY on the context, provide a concise, user-facing answer in 1-3 sentences.\n"
                    "If the context does not contain a direct answer, say you don't know.\n\n"
                    f"{prompt}\n\n"
                    "Answer:"
                )
                answer = (self.generator.generate(synthesis_prompt) or "").strip()
                if not answer:
                    answer = self._generate_simple_response(query, top_context)
            else:
                answer = self._generate_simple_response(query, top_context)
            
            # Clean, structured citations
            citations = self._format_citations(top_context)
            
            return {
                'answer': answer.strip(),
                'citations': citations,
                'context': [],  # hide raw chunks to avoid messy output
                'sources': list({c.get('source', 'kb') for c in top_context})
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
        
        # Heuristic concise summary from the first chunk
        txt = context[0].get('content', '').strip().replace('\n', ' ')
        txt = ' '.join(txt.split())  # collapse whitespace
        snippet = txt[:240].rstrip()
        if len(txt) > 240:
            snippet += '...'
        return f"Here's a concise summary based on the knowledge base: {snippet}"
    
    def _extract_citations(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deprecated: prefer _format_citations for structured citations."""
        return self._format_citations(context)
