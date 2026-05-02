# Use the official Python slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        "fastapi>=0.109.0" \
        "uvicorn[standard]>=0.25.0" \
        "httpx>=0.26.0" \
        "tiktoken>=0.5.0" \
        "sentence-transformers>=2.2.0" \
        "PyYAML>=6.0"

# Copy project source
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash tokcut && \
    chown -R tokcut:tokcut /app

USER tokcut

# Pre-download sentence-transformers model (cache warming)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || true

# Expose port
EXPOSE 8800

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8800/health || exit 1

# Run server
CMD ["python", "-m", "tokcut.server"]
