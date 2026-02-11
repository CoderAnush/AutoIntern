# AutoIntern AI — Copilot Instructions for AI Coding Agents

**Goal:** Help AI coding agents (Copilot, Claude, Cursor) be immediately productive in this monorepo by documenting the actual architecture, data flows, developer workflows, and project-specific patterns.

---

## 🎯 Quick Big Picture

**AutoIntern AI** is an AI-powered job & internship platform with a **production-ready microservices foundation**:

- **Monorepo structure** with 4 backend services under `services/`:
  - `api/` — FastAPI REST backend (job CRUD, admin DLQ management, health checks)
  - `worker/` — Async Redis consumer (processes jobs into PostgreSQL + Elasticsearch)
  - `scraper/` — Scrapy + Playwright (multi-site job web scraping)
  - `alert_receiver/` — Aiohttp webhook receiver (Alertmanager → HTTP)

- **Frontend:** React + Vite + Tailwind admin dashboard for DLQ inspection & requeue

- **Data Pipelines:**
  ```
  Scraper → Redis Queue → Worker → PostgreSQL (store) + Elasticsearch (index)
                          ↓
                      Prometheus
                      (metrics)
                            ↓
                    Admin UI (React)
  ```

- **Infrastructure:** Docker Compose orchestrates 8 services (Postgres, Redis, Elasticsearch, MinIO, Prometheus, Grafana, Alertmanager)

- **Monitoring:** Prometheus metrics, Grafana dashboards, Alertmanager alerts, custom alert receiver

---

## 📂 Must-Know Files & Entry Points

### Core Configuration
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates 8 services (ports, volume mounts, env vars) |
| `.env.example` | Canonical environment variables (copy to `.env` for local dev) |
| `.github/workflows/ci.yml` | GitHub Actions CI/CD (tests, migrations, E2E, linting) |

### Backend Services

**API Service** (`services/api/`)
| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app init, router registration, startup/shutdown hooks, metrics endpoint |
| `app/routes/health.py` | `GET /health`, `GET /health/db` endpoints |
| `app/routes/jobs.py` | `GET /jobs` (list), `POST /jobs` (create) with pagination & filtering |
| `app/routes/admin.py` | `GET /admin/dlq` (list failed messages), `POST /admin/dlq/requeue`, `DELETE /admin/dlq` |
| `app/routes/users.py` | `POST /users/register` (stub, to be completed) |
| `app/models/models.py` | SQLAlchemy ORM: User, Company, Job, Resume, Embedding, DLQItem tables |
| `app/schemas/job.py` | Pydantic request/response schemas for job data |
| `app/core/config.py` | Settings (env var parsing) using Pydantic Settings |
| `app/db/session.py` | Async SQLAlchemy session factory |
| `app/deps/redis.py` | Redis dependency injection for routes |
| `app/metrics.py` | Prometheus metrics (REQUEST_COUNT, PROCESSED counter, DLQ_SIZE gauge) |
| `alembic/` | Database migrations (Alembic ORM tool) |

**Worker Service** (`services/worker/`)
| File | Purpose |
|------|---------|
| `worker.py` | Main event loop (BRPOP Redis queue, retry logic, DLQ push) |
| `processor.py` | Parse job JSON → insert into PostgreSQL → index into Elasticsearch |
| `metrics.py` | Prometheus metrics server (processed count, DLQ gauge polling) |
| `utils.py` | Helper functions (ES indexing, JSON parsing) |

**Scraper Service** (`services/scraper/`)
| File | Purpose |
|------|---------|
| `autointern_scraper/spiders/base_spider.py` | Base class for all spiders (Playwright, proxy rotation, retry logic) |
| `scrapy.cfg` | Scrapy project config |

**Alert Receiver** (`services/alert_receiver/`)
| File | Purpose |
|------|---------|
| `app.py` | Aiohttp webhook server receiving alerts from Alertmanager (port 3005) |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/admin/src/App.jsx` | Root React component |
| `frontend/admin/src/pages/AdminDLQ.jsx` | DLQ inspection UI (list, delete, requeue with auth token) |
| `frontend/admin/vite.config.js` | Vite dev server & build config |
| `frontend/admin/cypress/e2e/admin_dlq.spec.js` | E2E tests for DLQ workflow |

### Infrastructure & Monitoring
| File | Purpose |
|------|---------|
| `infra/prometheus/prometheus.yml` | Scrape configs (targets: api:8000/metrics, worker:8001/metrics) |
| `infra/prometheus/alert.rules.yml` | Alert rules (HighDLQSize, WorkerFailureSpike) |
| `infra/grafana/dashboards/full_dashboard.json` | Comprehensive metrics dashboard |
| `infra/grafana/dashboards/dlq_dashboard.json` | DLQ-focused dashboard |
| `infra/alertmanager/alertmanager.yml` | Alert routing config |

### Scripts & Tests
| File | Purpose |
|------|---------|
| `scripts/dlq_cli.py` | CLI tool: list/requeue/delete DLQ items from Redis |
| `scripts/push_dlq.py` | Push test job payload to Redis queue for testing |
| `scripts/send_test_alert.py` | Send test alert to Alertmanager (smoke test) |
| `scripts/run_migrations.ps1` | PowerShell helper to run Alembic migrations |
| `scripts/setup_dev.ps1` | Windows dev setup (copy `.env.example`, start docker compose) |
| `tests/test_health.py` | API health endpoint tests |

---

## 🔄 Developer Workflows (Exact Commands)

### Local Development Setup

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start all 8 services (Postgres, Redis, ES, MinIO, API, Worker, Prometheus, Grafana)
docker compose up --build

# 3. In a new terminal, run migrations (inside API container)
docker compose exec api alembic -c alembic.ini upgrade head

# 4. Access services:
#    - API: http://localhost:8000 (OpenAPI docs at /docs)
#    - Admin UI: http://localhost:3000 (login with admin token from .env)
#    - Prometheus: http://localhost:9090
#    - Grafana: http://localhost:3000 (admin/admin)
#    - Elasticsearch: http://localhost:9200
#    - MinIO: http://localhost:9000
```

### Running Tests

```bash
# Install dependencies (from repo root)
pip install -r services/api/requirements.txt
pip install -r services/worker/requirements.txt

# Run unit & integration tests
pytest -q

# Run E2E tests (Cypress) — requires frontend running on :3000
cd frontend/admin
npm install
npm run build
npm run preview  # or dev for hot reload
# In another terminal:
npx cypress run --spec "cypress/e2e/admin_dlq.spec.js"
```

### Running the Scraper

```bash
cd services/scraper

# Install Playwright browsers (one-time)
playwright install

# Run a specific spider
scrapy crawl <spider_name>
```

### Database Migrations

```bash
# Inside services/api directory:

# Generate a new migration (auto-detects model changes)
alembic revision --autogenerate -m "add new field to jobs table"

# Apply pending migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View migration history
alembic history
```

**Note:** In development, set `MIGRATE_ON_START=true` in `.env` to auto-create tables on API startup (not for production).

### Local API Development (without Docker)

```bash
cd services/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set DATABASE_URL and other env vars (or load .env)
export DATABASE_URL="postgresql+asyncpg://autointern:change-me@localhost:5432/autointern"
export REDIS_URL="redis://localhost:6379"

# Run uvicorn with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Admin DLQ Workflow

```bash
# 1. Push a test job to the queue
python scripts/push_dlq.py

# 2. Trigger failure (worker will retry, then move to DLQ after max attempts)
# Watch DLQ grow via:
python scripts/dlq_cli.py list

# 3. Inspect/requeue via CLI
python scripts/dlq_cli.py requeue <message_id>
# OR via Admin UI at http://localhost:3000

# 4. Smoke test alerting
python scripts/send_test_alert.py
```

---

## 🏗️ Architecture & Data Flows

### Job Ingestion Pipeline

```
┌─────────────────────────────────────────────┐
│ 1. Scraper (Scrapy × Playwright)            │
│    Fetches jobs from 100+ sites             │
│    Outputs normalized JSON: {title, desc,   │
│    location, source, url, company}          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ 2. Redis Queue (ingest:jobs)                │
│    Decouples scraper from processor         │
│    Allows retry & DLQ management            │
└────────────────┬────────────────────────────┘
                 │
                 ▼ BRPOP (blocking)
┌─────────────────────────────────────────────┐
│ 3. Worker (async consumer)                  │
│    Retry logic: 3 attempts max              │
│    Failed → DLQ (ingest:dlq)                │
└────┬────────────────────────────────┬───────┘
     │                                │
     ▼ on success                     ▼ on final failure
┌─────────────────────────────────────────────┐
│ PostgreSQL             │         Redis       │
│ ├─ Jobs table (store)  │         DLQ        │
│ └─ Dedup via signature │                    │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│ Elasticsearch                               │
│ (autointern-jobs index, full-text search)  │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│ Prometheus (worker exports)                 │
│ ├─ PROCESSED counter (success/failure)      │
│ ├─ DLQ_SIZE gauge (polled every 30s)        │
│ └─ REQUEST_COUNT (API middleware)           │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│ Grafana Dashboards + Alertmanager Alerts    │
│ Alert: HighDLQSize (> 5 items for 1 min)   │
└─────────────────────────────────────────────┘
```

### Admin DLQ Recovery

```
┌──────────────────────────────────────────────┐
│ Admin UI (React, http://localhost:3000)      │
│ ├─ Login with ADMIN_API_KEY from .env        │
│ ├─ List DLQ items (GET /admin/dlq)           │
│ ├─ Requeue (POST /admin/dlq/requeue)         │
│ └─ Delete (DELETE /admin/dlq)                │
└────┬─────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────┐
│ FastAPI /admin/* endpoints (token-verified)  │
│ Auth: Bearer <admin_api_key> in Authorization│
└────┬─────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────┐
│ Redis: requeue moves from DLQ to ingest:jobs │
│ Worker will process retry on next poll cycle │
└──────────────────────────────────────────────┘
```

---

## 📋 Project-Specific Conventions & Patterns

### Monorepo Organization
- **Each service** has its own `Dockerfile`, `requirements.txt`, and startup logic
- **Environment variables** loaded from `.env` via `python-dotenv` and Pydantic `Settings`
- **Shared utilities** (if needed) go under `scripts/` or a separate `lib/` directory (not yet created)

### Database Patterns
- Models use **PostgreSQL-specific types**: UUID (not Int), JSONB (for embeddings)
- **Deduplication:** Jobs use `dedupe_signature` (hash of title + company + location) to prevent duplicates
- **Async ORM:** SQLAlchemy 2.0 with `asyncpg` driver for non-blocking DB calls
- **Always use Alembic** for schema changes — never modify `Base.metadata` directly in production

### Redis Queue Patterns
- **BRPOP with timeout=1s** prevents busy-waiting; worker sleeps 0.1s between cycles
- **Retry tracking:** `message['_attempts']` incremented per retry
- **DLQ format:** Failed messages include `_error` and `_attempts` metadata
- **Max retries:** Configurable via `WORKER_MAX_RETRIES` env var (default 3)

### Elasticsearch Patterns
- **Index naming:** `autointern-jobs` + date suffixes (e.g., `autointern-jobs-2024-02-11`)
- **Mapping:** Full-text search on title, description, company name
- **Bulk indexing:** Worker batches inserts if processing multiple jobs per second
- **No deletes in worker:** Soft-deletion via status field (not yet implemented but planned)

### Frontend Patterns (React Admin UI)
- **State management:** Component-level state (useState) for DLQ items; localStorage for auth token
- **API calls:** Axios with Bearer token in Authorization header
- **Error handling:** Toast/alert notifications (not yet fully wired but scaffold in place)
- **Styling:** Tailwind CSS (no component library; raw utility classes)

### Testing Patterns
- **Unit tests:** Test parsing logic, dedup logic in isolation using fixtures
- **Integration tests:** Use Docker testcontainers or live services for API/Worker tests
- **E2E tests:** Cypress tests for critical admin UI workflows (requeue, delete, list)
- **No mocking of external services in CI** — services are spun up via Docker Compose in CI

### Monitoring & Alerting Patterns
- **Prometheus:** Custom metrics exposed at `/metrics` endpoint (Prometheus text format)
- **Alert rules:** YAML-based rules in `infra/prometheus/alert.rules.yml`
- **Alert routing:** Alertmanager webhook → alert_receiver service (http://localhost:3005)
- **Dashboards:** Grafana auto-provisions dashboards from JSON files in `infra/grafana/dashboards/`

---

## 🔗 Integration Points & External Dependencies

| Service | URL | Purpose | When Used |
|---------|-----|---------|-----------|
| **PostgreSQL** | `localhost:5432` | Persistent job storage | Always (every API call, worker) |
| **Redis** | `localhost:6379` | Job queue & DLQ | Scraper (push), Worker (consume) |
| **Elasticsearch** | `localhost:9200` | Full-text search index | Worker (index after DB insert) |
| **MinIO** | `localhost:9000` | S3-compatible object storage | Resume uploads (not yet wired) |
| **Prometheus** | `localhost:9090` | Metrics scraping | Admin/DevOps (dashboards) |
| **Grafana** | `localhost:3000` | Metrics visualization | Admin/DevOps (dashboards) |
| **Alertmanager** | `localhost:9093` | Alert routing | Prometheus → Webhook |

### Scrapy Spider Development Checklist
1. Define spider class in `services/scraper/autointern_scraper/spiders/<name>_spider.py`
2. Subclass `BaseJobSpider` (includes Playwright, proxy rotation, ban detection)
3. Implement `parse()` and XPath/CSS selectors for job extraction
4. Add fixtures (sample HTML) to `tests/fixtures/<site>_sample.html`
5. Unit test parsing logic against fixtures
6. Add spider name to `scrapy.cfg` settings
7. Push jobs to Redis: `redis.lpush("ingest:jobs", json.dumps(job_dict))`
8. **Do not** add LinkedIn, Indeed, or sites with restrictive ToS without explicit owner approval

---

## 🚀 Development Norms for AI Agents

### PR & Commit Strategy
- **Always open draft PRs** on a feature branch (e.g., `dev/add-indeed-spider`, `dev/fix-dlq-auth`)
- **Never commit/push directly to main** without explicit user approval
- Reference this document in PR descriptions to link to architectural decisions
- Small, focused PRs (one feature or fix per PR)

### Code Quality
- **Tests required** for all new features: unit tests + integration tests where applicable
- **Run `pytest -q` locally** before pushing to verify all tests pass
- **Lint with ruff** (included in CI)
- **Database changes:** Always add Alembic migration files; include migration instructions in PR body

### Documentation
- **Update `.env.example`** when adding new env vars
- **Add docstrings** to new route functions and worker processors (one-line minimum)
- **Update this file** if adding new patterns or conventions

---

## 🐛 Diagnostics & Debugging Tips

### Common Issues

**Tests fail with "module not found"**
```bash
pip install -r services/api/requirements.txt
pip install -r services/worker/requirements.txt
```

**Database connection timeout**
```bash
# Wait for PostgreSQL to be ready (docker compose logs postgres)
# Then run migrations:
docker compose exec api alembic -c alembic.ini upgrade head
```

**Elasticsearch not indexing**
```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check index mappings
curl http://localhost:9200/autointern-jobs/_mappings

# Inspect job processing logs
docker compose logs worker | grep -i error
```

**Admin UI auth token not working**
```bash
# Verify ADMIN_API_KEY in .env is set
echo $ADMIN_API_KEY

# Test token manually
curl -H "Authorization: Bearer $ADMIN_API_KEY" http://localhost:8000/admin/dlq
```

**Prometheus not scraping metrics**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify API /metrics endpoint responds
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
```

### Debugging Tools
- **API:** OpenAPI/Swagger at `http://localhost:8000/docs`
- **Worker:** Check logs: `docker compose logs worker -f`
- **Redis CLI:** `docker compose exec redis redis-cli`
- **PostgreSQL CLI:** `docker compose exec postgres psql -U autointern -d autointern`
- **Elasticsearch Query:** `curl -X GET http://localhost:9200/autointern-jobs/_search?q=*`

---

## 🔐 Security & Legal Notes

- **Never commit secrets:** Use `.env` (in `.gitignore`) for local development, HashiCorp Vault or similar in production
- **Admin token protection:** Keep `ADMIN_API_KEY` private; rotate in production
- **Scraper ToS compliance:** Document legal considerations for each site in `docs/legal.md` (not yet created)
- **Resume data:** Treat as PII; ensure encrypted storage in MinIO + access logs in production

---

## 📈 Roadmap & TODOs

**Implemented (MVP):**
- ✅ API with job CRUD and admin DLQ endpoints
- ✅ Redis job queue with retry & DLQ
- ✅ Worker: process jobs → PostgreSQL + Elasticsearch
- ✅ Prometheus metrics & Grafana dashboards
- ✅ React admin UI for DLQ management
- ✅ E2E testing (Cypress)
- ✅ CI/CD (GitHub Actions)
- ✅ Docker Compose orchestration

**In Progress / To-Do:**
- 🚧 Resume parsing & skill extraction (processor service stub exists)
- 🚧 Semantic job-candidate matching (Sentence-BERT + FAISS)
- 🚧 User authentication (JWT tokens scaffolded, login UI needed)
- 🚧 Multi-site scraper (base spider template ready, 10+ sites needed)
- 🚧 Email notifications & dashboard alerts
- 🚧 Advanced Grafana dashboards (SLA, job volume trends)
- 🚧 Kubernetes deployment configs (helm charts)
- 🚧 API rate limiting & quotas
- 🚧 Soft deletion & archival for old jobs

---

## 📚 When You Need More Context

- **Architecture details:** See `services/api/README.md` and `services/scraper/README.md`
- **Monitoring setup:** See `infra/prometheus/alert.rules.d/README.md`
- **Legal/ethical concerns:** Create `docs/legal.md` documenting site scraping policies
- **AI/ML components:** Processor and ai_engine services are scaffolds; coordinate with product on approach

---

**This file was auto-generated from codebase analysis. Update when significant architectural changes occur.**
