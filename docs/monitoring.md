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

Smoke test (optional in CI):
- Set the environment variable `RUN_MONITORING_TESTS=true` in CI to enable the smoke test. The CI step will:
  - Wait for `alert-receiver` to be healthy
  - Send a test alert to Alertmanager: `scripts/send_test_alert.py --alert CI_SmokeTest`
  - Poll the `alert-receiver` `/alerts` endpoint until it sees the test alert (or fail after timeout)

Next steps:
- Provision a Grafana dashboard to visualize DLQ growth, processed rates, and API errors.
- Add alerting rules (Prometheus Alertmanager) to notify when DLQ or failure rates exceed thresholds.
- Use `infra/alertmanager/secrets/` to mount production secrets; see `infra/alertmanager/secrets.README.md`.
