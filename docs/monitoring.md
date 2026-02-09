# Monitoring & Metrics

This project uses Prometheus for metrics collection and Grafana for visualization.

Setup (local dev):
- Ensure `.env` is configured and run `docker compose up --build`.
- Prometheus UI: http://localhost:9090
- Grafana UI: http://localhost:3000 (admin/admin)

Metrics:
- API exposes `/metrics` on port 8000. Key metrics:
  - `api_requests_total{method,endpoint,status}` — counts of HTTP requests
  - `api_jobs_created_total` — number of jobs created via API
- Worker exposes Prometheus server on port 8001. Key metrics:
  - `worker_processed_total{result}` — counts with labels `result=success|failure` (incremented in worker)
  - `worker_dlq_size` (gauge) — current size of the DLQ Redis list

Prometheus configuration is in `infra/prometheus/prometheus.yml` and is included in `docker-compose.yml` for local development.

Next steps:
- Provision a Grafana dashboard to visualize DLQ growth, processed rates, and API errors.
- Add alerting rules (Prometheus Alertmanager) to notify when DLQ or failure rates exceed thresholds.
