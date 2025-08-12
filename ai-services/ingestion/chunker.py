"""
Text chunking utilities for document processing.
"""
import re
import nltk
from typing import List, Dict, Any
from dataclasses import dataclass
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    text: str
    metadata: Dict[str, Any]
    chunk_id: str = ""
    embedding: List[float] = None

class SemanticChunker:
    """
    Chunk text into semantically meaningful pieces.
    Attempts to keep paragraphs, sentences, and other structural elements together.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    
    def chunk_document(self, text: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
        """
        Split a document into chunks.
        
        Args:
            text: The text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of TextChunk objects
        """
        if metadata is None:
            metadata = {}
            
        # First try to split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If paragraph is too long, split into sentences
            if len(para) > self.chunk_size * 1.5:
                sentences = self.sentence_tokenizer.tokenize(para)
                for sentence in sentences:
                    if current_length + len(sentence) > self.chunk_size and current_chunk:
                        chunks.append(self._create_chunk(current_chunk, metadata))
                        current_chunk = []
                        current_length = 0
                    current_chunk.append(sentence)
                    current_length += len(sentence)
            else:
                if current_length + len(para) > self.chunk_size and current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(para)
                current_length += len(para)
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata))
        
        # Add overlapping chunks if needed
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlapping_chunks(chunks)
        
        return chunks
    
    def _create_chunk(self, text_parts: List[str], metadata: Dict[str, Any]) -> TextChunk:
        """Create a TextChunk from text parts."""
        text = '\n\n'.join(text_parts)
        return TextChunk(
            text=text,
            metadata=metadata.copy(),
            chunk_id=self._generate_chunk_id(text, metadata)
        )
    
    def _add_overlapping_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Add overlapping chunks to improve context."""
        if len(chunks) <= 1:
            return chunks
            
        overlapping_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Get the end of the previous chunk
            prev_text = prev_chunk.text
            overlap_start = max(0, len(prev_text) - self.chunk_overlap)
            overlap_text = prev_text[overlap_start:]
            
            # Create new chunk with overlap
            new_chunk = TextChunk(
                text=overlap_text + '\n\n' + current_chunk.text,
                metadata=current_chunk.metadata.copy(),
                chunk_id=self._generate_chunk_id(current_chunk.text, current_chunk.metadata)
            )
            
            overlapping_chunks.append(new_chunk)
        
        return overlapping_chunks
    
    @staticmethod
    def _generate_chunk_id(text: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique ID for a chunk."""
        import hashlib
        source = metadata.get('source', 'unknown')
        chunk_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        return f"{source}:{chunk_hash}"

# Default chunker instance
default_chunker = SemanticChunker()
