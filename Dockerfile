# Use Python 3.11 slim image (Debian-based for better package compatibility)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libsndfile1 \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV for faster dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using UV
RUN uv sync --frozen

# Create necessary directories with proper permissions
RUN mkdir -p uploads logs vector_db models && \
    chmod 755 uploads logs vector_db models

# Copy application code
COPY . .

# Set environment variables for file processing
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MAX_UPLOAD_SIZE=100MB
ENV PROCESSING_TIMEOUT=300

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
