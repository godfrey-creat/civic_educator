# Use Python 3.8 slim as the base image
FROM python:3.8-slim

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

# Copy wheels and requirements
COPY wheels /wheels
COPY requirements.txt .

# Install Python dependencies from wheels and requirements.txt
RUN pip install --no-cache-dir /wheels/* && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure required directories exist
RUN mkdir -p /app/indexes /app/knowledge_base

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
