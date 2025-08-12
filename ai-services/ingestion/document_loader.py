"""
Document loading and processing utilities for various file formats.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import fitz  # PyMuPDF
import docx
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin

from config import settings

logger = logging.getLogger(__name__)

class DocumentLoader:
    """Load and process documents from various formats and sources."""
    
    @staticmethod
    def load_document(file_path: Union[str, Path]) -> Dict[str, str]:
        """Load a document from file path."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() == '.pdf':
            return DocumentLoader._load_pdf(file_path)
        elif file_path.suffix.lower() == '.docx':
            return DocumentLoader._load_docx(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md']:
            return DocumentLoader._load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    @staticmethod
    def _load_pdf(file_path: Path) -> Dict[str, str]:
        """Extract text from PDF file."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return {
                "content": text,
                "metadata": {
                    "source": str(file_path),
                    "type": "pdf",
                    "pages": len(doc)
                }
            }
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def _load_docx(file_path: Path) -> Dict[str, str]:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return {
                "content": text,
                "metadata": {
                    "source": str(file_path),
                    "type": "docx"
                }
            }
        except Exception as e:
            logger.error(f"Error loading DOCX {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def _load_text(file_path: Path) -> Dict[str, str]:
        """Load text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "content": content,
                "metadata": {
                    "source": str(file_path),
                    "type": "text"
                }
            }
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {str(e)}")
            raise
    
    @staticmethod
    async def load_from_url(url: str) -> Dict[str, str]:
        """Load document from URL (PDF, HTML, etc.)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch {url}: {response.status}")
                    
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/pdf' in content_type:
                        return await DocumentLoader._load_pdf_from_response(url, response)
                    else:
                        return await DocumentLoader._load_webpage(url, response)
        except Exception as e:
            logger.error(f"Error loading from URL {url}: {str(e)}")
            raise
    
    @staticmethod
    async def _load_pdf_from_response(url: str, response) -> Dict[str, str]:
        """Load PDF from HTTP response."""
        content = await response.read()
        with fitz.open(stream=content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return {
                "content": text,
                "metadata": {
                    "source": url,
                    "type": "pdf",
                    "pages": len(doc)
                }
            }
    
    @staticmethod
    async def _load_webpage(url: str, response) -> Dict[str, str]:
        """Extract main content from webpage."""
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return {
            "content": text,
            "metadata": {
                "source": url,
                "type": "webpage",
                "title": soup.title.string if soup.title else ""
            }
        }
