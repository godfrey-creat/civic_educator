# Civic Educator AI Service

An AI-powered microservice for document retrieval and question answering focused on Kenyan government services and civic education.

## Features

- Document ingestion from various sources (PDF, DOCX, web pages)
- Semantic search with hybrid retrieval (dense + sparse)
- RAG (Retrieval-Augmented Generation) for question answering
- RESTful API with FastAPI
- Containerized with Docker for easy deployment

## Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- Git

## Quick Start

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/civic-educator-ai.git
   cd civic-educator-ai/ai-services
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the service:
   ```bash
   uvicorn api.app:app --reload
   ```

6. Access the API documentation at: http://localhost:8000/docs

### Docker Deployment

1. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```

2. The service will be available at: http://localhost:8000

## API Endpoints

### Search Documents
```
GET /api/v1/search?query=your+query&top_k=5
```

### Ask a Question
```
POST /api/v1/ask
{
    "question": "What are the requirements for a business permit?",
    "top_k": 3,
    "max_length": 500,
    "temperature": 0.7
}
```

### Health Check
```
GET /health
```

## Project Structure

```
ai-services/
├── api/                       # API endpoints
│   ├── app.py                 # FastAPI application
│   ├── routes_retrieval.py    # Document search endpoints
│   └── routes_generation.py   # Question answering endpoints
│
├── config/                    # Configuration
│   ├── settings.py            # Application settings
│   └── constants.py           # Constants and enums
│
├── ingestion/                 # Document processing
│   ├── document_loader.py     # Document loading
│   ├── chunker.py             # Text chunking
│   └── index_builder.py       # Search index management
│
├── models/                    # ML models
│   ├── embeddings.py          # Text embedding models
│   └── reranker.py            # Result reranking
│
├── rag/                       # RAG pipeline
│   ├── retriever.py           # Document retrieval
│   ├── generator.py           # Answer generation
│   └── pipeline.py            # End-to-end pipeline
│
├── tests/                     # Unit and integration tests
│   └── ...
│
├── .env.example               # Example environment variables
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Adding Documents

1. Place your documents in the `knowledge_base/sourced_pdfs` directory
2. The service will automatically index them on startup

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
isort .
```

### Linting
```bash
flake8 .
mypy .
pylint **/*.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Sentence Transformers](https://www.sbert.net/) for text embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for efficient similarity search
- [Hugging Face](https://huggingface.co/) for pre-trained models
