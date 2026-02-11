# Routes package
# Only import health router; other routers have external service dependencies
# that may not be available at startup (MinIO, embeddings service, etc.)
from . import health
