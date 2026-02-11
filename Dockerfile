# Multi-stage build for AutoIntern API Production
FROM python:3.10-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Production stage
FROM base as production

# Copy API requirements
COPY services/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/api/. /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; import requests; import os; port = os.environ.get('PORT', '8000'); sys.exit(0 if requests.get(f'http://localhost:{port}/health').status_code == 200 else 1)" || true

# Run with uvicorn (production-grade ASGI server) - use PORT from environment (Railway) or default to 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
