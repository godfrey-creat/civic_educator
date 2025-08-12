import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, HttpUrl, validator
from pydantic_settings import BaseSettings
from pydantic.networks import AnyHttpUrl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden by environment variables with the same name.
    For example, to override the API prefix, set API_PREFIX in your .env file.
    """
    
    # --- Application Settings ---
    APP_NAME: str = Field("Civic Educator AI", 
                         description="Name of the application")
    DEBUG: bool = Field(False, 
                       env="DEBUG",
                       description="Enable debug mode (more verbose logging)")
    ENVIRONMENT: str = Field("production", 
                           env="ENVIRONMENT",
                           description="Runtime environment (e.g., development, staging, production)")
    
    # --- API Settings ---
    API_PREFIX: str = Field("/api/v1", 
                           description="API URL prefix (e.g., /api/v1)")
    HOST: str = Field("0.0.0.0", 
                     env="HOST",
                     description="Host to bind the API server")
    PORT: int = Field(8000, 
                     env="PORT",
                     description="Port to bind the API server")
    ROOT_PATH: str = Field("", 
                          env="ROOT_PATH",
                          description="Root path for API (useful for proxies)")
    
    # --- CORS Settings ---
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS",
        description="List of allowed CORS origins"
    )
    
    # --- Model Settings ---
    EMBEDDING_MODEL: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL",
        description="Sentence transformer model for embeddings"
    )
    RERANKER_MODEL: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        env="RERANKER_MODEL",
        description="Cross-encoder model for reranking"
    )
    
    # --- Document Processing ---
    CHUNK_SIZE: int = Field(
        1000,
        env="CHUNK_SIZE",
        description="Size of text chunks for document processing"
    )
    CHUNK_OVERLAP: int = Field(
        200,
        env="CHUNK_OVERLAP",
        description="Overlap between chunks for document processing"
    )
    
    # --- RAG Pipeline ---
    MAX_RETRIEVED_DOCS: int = Field(
        5,
        env="MAX_RETRIEVED_DOCS",
        description="Maximum number of documents to retrieve"
    )
    CONFIDENCE_THRESHOLD: float = Field(
        0.7,
        env="CONFIDENCE_THRESHOLD",
        description="Minimum confidence score for high-confidence answers"
    )
    SCORE_THRESHOLD: float = Field(
        0.5,
        env="SCORE_THRESHOLD",
        description="Minimum relevance score for document retrieval"
    )
    
    # --- Paths ---
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = Field(
        BASE_DIR / "data",
        description="Base directory for data storage"
    )
    INDEX_DIR: Path = Field(
        BASE_DIR / "data/index",
        description="Directory for storing vector indices"
    )
    DOCUMENTS_DIR: Path = Field(
        BASE_DIR / "data/documents",
        description="Directory containing source documents"
    )
    
    # --- Logging ---
    LOG_LEVEL: str = Field(
        "INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # --- Security ---
    SECRET_KEY: str = Field(
        "change-this-in-production",
        env="SECRET_KEY",
        description="Secret key for cryptographic operations"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 7,  # 7 days
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT token expiration time in minutes"
    )
    
    # --- API Keys (Optional) ---
    OPENAI_API_KEY: Optional[str] = Field(
        None,
        env="OPENAI_API_KEY",
        description="OpenAI API key (if using OpenAI models)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            """Parse environment variable values based on field type."""
            if field_name == "CORS_ORIGINS":
                return [origin.strip() for origin in raw_val.split(",") if origin.strip()]
            return cls.json_loads(raw_val)
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("ENVIRONMENT")
    def env_must_be_valid(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production", "test"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {', '.join(valid_envs)}")
        return v.lower()
    
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"

# Document Sources
DOCUMENT_SOURCES = {
    "nairobi_county": {
        "name": "Nairobi County Government",
        "base_url": "https://nairobi.go.ke",
        "documents": [
            "county-act-2016.pdf",
            "service-charter.pdf"
        ]
    },
    "national_government": {
        "name": "Kenya National Government",
        "base_url": "https://www.parliament.go.ke",
        "documents": [
            "constitution-of-kenya-2010.pdf",
            "data-protection-act-2019.pdf"
        ]
    }
}

# Create settings instance
settings = Settings()

# Ensure required directories exist
settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
