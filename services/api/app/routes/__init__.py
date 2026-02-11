# Routes package
# All routers properly handle external service initialization:
# - health: No external dependencies
# - users: Uses dependency injection for database
# - jobs: Lazy loads embeddings manager on first use
# - resumes: Lazy loads MinIO client on first use
# - recommendations: Lazy loads embeddings manager on first use
# - admin: Uses dependency injection for Redis
from . import health, users, jobs, resumes, recommendations, admin
