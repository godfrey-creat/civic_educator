# Civic Educator AI Service

An AI-powered microservice for document retrieval and question answering focused on Kenyan government services and civic education.

---

## AI Services – Local Development Guide

This guide explains how to set up and run the AI Services project locally using Docker, and how to build or refresh the document index.

### 1. Prerequisites

- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/
- Optional: Python 3.8+ & virtualenv (for local development outside Docker)

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd ai-services
```

### 3. Build the Docker Image

```bash
docker compose build
```

If you’ve made changes to dependencies or the Dockerfile, build without cache:

```bash
docker compose build --no-cache
```

### 4. Start the Services

```bash
docker compose up
```

The API will be available at:

```
http://127.0.0.1:8000
```

### 5. Building the Index

You must build the document index before using RAG features.

First run (or after adding new documents):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/reindex
```

Example response:

```json
{
  "indexed_docs": 25,
  "indexed_chunks": 320
}
```

This scans documents under `knowledge_base/sourced_pdfs/` and builds a FAISS index in `data/index/`.

### 6. API Documentation

Open the interactive docs at:

```
http://127.0.0.1:8000/docs
```

### 7. Stopping the Services

Press `Ctrl + C` in the terminal where `docker compose up` is running, or run:

```bash
docker compose down
```

### 8. Troubleshooting

- **Module not found errors inside Docker**: Ensure packages are in `requirements.txt`, then rebuild

  ```bash
  docker compose build --no-cache
  ```

- **Index not found errors**: Build (or rebuild) the index

  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/reindex
  ```

- **Reindex is slow on first run**: Models are downloading and documents are being chunked/embedded. Subsequent runs are faster with the HF cache (see below).

### 9. Knowledge Base Location

- Place your documents under: `knowledge_base/sourced_pdfs/`
- The service walks this directory when building or rebuilding the index.

### 10. Hugging Face Cache (Speed Up Model Downloads)

The compose file mounts a persistent cache so model downloads are reused across runs:

- Volume: `./hf-cache:/root/.cache/huggingface`
- Env: `HF_HOME=/root/.cache/huggingface`, `TRANSFORMERS_CACHE=/root/.cache/huggingface`

Create the directory if it doesn’t exist:

```bash
mkdir -p hf-cache
```

### 11. Environment Variables

- `GOOGLE_API_KEY` (optional): Enables Gemini fallback for general questions. Add to your `.env` and compose will pass it through.

```bash
echo GOOGLE_API_KEY=your_key_here > .env
docker compose up --build
```

### 12. Example Workflow

1) Start Docker

```bash
docker compose up
```

2) Index documents

```bash
curl -X POST http://127.0.0.1:8000/api/v1/reindex
```

3) Use the API

Visit `http://127.0.0.1:8000/docs` and try the endpoints.

---

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
