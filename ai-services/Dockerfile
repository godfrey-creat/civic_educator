# Use Python 3.10 slim as the base image
FROM python:3.10-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (so wheel caching works)
COPY requirements.txt .

# Pre-build wheels inside the container for Python 3.10
RUN pip install --upgrade pip && \
    mkdir -p /wheels && \
    pip wheel --wheel-dir=/wheels -r requirements.txt

# Install dependencies from wheels
RUN pip install --no-cache-dir /wheels/*

# Copy rest of the application code
COPY . .

# Ensure required directories exist
RUN mkdir -p /app/indexes /app/knowledge_base

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
