FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY notebooks/ ./notebooks/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p data/raw data/processed reports db

# Default command runs the full pipeline
CMD ["python", "-m", "src.ingest"]