from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry

# Global registry for this service
REGISTRY = CollectorRegistry(auto_describe=True)

REQUEST_COUNT = Counter("api_requests_total", "Total API requests", ["method", "endpoint", "status"], registry=REGISTRY)
JOB_CREATE_COUNT = Counter("api_jobs_created_total", "Total jobs created via API", registry=REGISTRY)


def metrics_response():
    data = generate_latest(REGISTRY)
    return data, CONTENT_TYPE_LATEST
