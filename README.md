# AutoIntern AI

**An AI-powered job & internship aggregation and recommendation platform for students and entry-level engineers.**

## 📊 Project Status

- **Completion:** 60% MVP (infrastructure complete) → 100% Feature-Complete Product
- **Timeline:** 10 weeks to full launch
- **Stack:** FastAPI, Scrapy, React, PostgreSQL, Redis, Elasticsearch, Sentence-BERT

**Already Built:**
- ✅ Production-ready API (FastAPI)
- ✅ Redis queue + DLQ system
- ✅ Worker service (processes jobs)
- ✅ React admin UI
- ✅ Prometheus + Grafana monitoring
- ✅ CI/CD pipeline
- ✅ Docker Compose orchestration

**Remaining Work:**
- 🚧 Web scrapers (Indeed, Wellfound, etc.)
- 🚧 Resume parsing & skill extraction
- 🚧 AI embeddings & job recommendations
- 🚧 User authentication & dashboard
- 🚧 Email notifications
- 🚧 Kubernetes deployment

---

## 🚀 Quick Start

### 1. Read the Guides
- **[QUICK_START.md](./QUICK_START.md)** — Executive summary + dev workflow
- **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** — 10-week phase-by-phase plan
- **[.github/copilot-instructions.md](./.github/copilot-instructions.md)** — Architecture for AI agents

### 2. Setup Local Environment
```bash
# Copy environment template
cp .env.example .env

# Start all services (Docker required)
docker compose up --build

# In another terminal, run migrations
docker compose exec api alembic -c alembic.ini upgrade head

# Verify setup
curl http://localhost:8000/health  # API health check
open http://localhost:8000/docs     # API docs
```

### 3. Start Development
```bash
# Create feature branch
git checkout -b dev/your-feature-name

# Follow IMPLEMENTATION_ROADMAP.md for Phase 1 (If starting with spiders)
# or Phase 5 (If starting with auth)

# Run tests
pytest -q
```

---

## 📂 Directory Structure

```
AutoIntern/
├── services/
│   ├── api/              # FastAPI REST backend (job CRUD, admin endpoints)
│   ├── worker/           # Async Redis consumer (processes jobs)
│   ├── scraper/          # Scrapy + Playwright spiders (to implement)
│   ├── processor/        # Resume parsing + skill extraction (scaffolded)
│   ├── ai_engine/        # Embeddings & recommendations (scaffolded)
│   ├── notifications/    # Email alerts (scaffolded)
│   └── alert_receiver/   # Alertmanager webhook receiver
├── frontend/
│   └── admin/            # React admin dashboard (DLQ management)
├── infra/
│   ├── prometheus/       # Metrics & alert rules
│   ├── grafana/          # Dashboards
│   └── alertmanager/     # Alert routing
├── tests/                # Integration tests
├── scripts/              # CLI tools (dlq_cli, push_dlq, etc.)
├── docs/                 # Architecture docs
└── docker-compose.yml    # Local dev orchestration
```

---

## 📚 System Architecture

```
Job Sources (Spiders)
    ↓
Redis Queue (ingest:jobs)
    ↓
Worker Service (async consumer)
    ↓ (on success)
┌─────────────────────────────────┐
│ PostgreSQL + Elasticsearch      │
│ (storage + full-text search)    │
└─────────────────────────────────┘
    ↓
Prometheus (metrics)
    ↓
Grafana (dashboards)
    ↓
API → React Dashboard (job search, recommendations)
```

**Key Features:**
- **Retry Logic:** Jobs retry 3 times; failed jobs move to DLQ
- **Deduplication:** Prevents duplicate job entries via signature hashing
- **Full-Text Search:** Elasticsearch indexes all jobs (title, description, company)
- **Recommendations:** Sentence-BERT embeddings + cosine similarity matching
- **Monitoring:** Real-time metrics, alerts for failures
- **Admin Tools:** UI for inspecting/requeuing failed jobs

---

## 🎯 Next Steps

### Option 1: Data Pipeline (Recommended for MVP)
**Phase 1 (Week 1-2):** Implement 5 job portal spiders
- Indeed (highest volume)
- Wellfound (startup internships)
- RemoteOK (remote work)
- WeWorkRemotely (tech remote)
- LinkedIn (via API only)

**Result:** 50k+ searchable tech jobs

### Option 2: User Features (Recommended if starting fresh)
**Phase 5 (Week 5-6):** Build authentication + login UI
- JWT tokens + local authentication
- React login form
- User dashboard

**Result:** Users can register, login, browse jobs

### Option 3: AI Features
**Phase 4 (Week 4-5):** Add job recommendations
- Sentence-BERT embeddings
- FAISS indexing
- Cosine similarity matching

**Result:** Personalized job recommendations

---

## 🔧 Development

### Running Services Locally

**Just the API:**
```bash
cd services/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://autointern:change-me@localhost:5432/autointern"
uvicorn app.main:app --reload
```

**Run Scraper:**
```bash
cd services/scraper
playwright install  # One-time setup
scrapy crawl <spider_name>
```

**Run Worker:**
```bash
cd services/worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python worker.py
```

### Testing

```bash
# Unit + Integration tests
pytest -q

# E2E tests (requires services running)
cd frontend/admin
npm run cypress:run

# Specific test
pytest tests/test_health.py -v
```

### Database Migrations

```bash
cd services/api

# Generate migration (auto-detect model changes)
alembic revision --autogenerate -m "add new field"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 📊 Monitoring & Debugging

### Check System Health
```bash
# API
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# Worker
curl http://localhost:8001/metrics

# Queue status
docker compose exec redis redis-cli LLEN ingest:jobs

# Elasticsearch
curl http://localhost:9200/_cluster/health

# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3000 (admin/admin)
```

### View Logs
```bash
docker compose logs api -f       # API service
docker compose logs worker -f    # Worker service
docker compose logs postgres -f  # Database
```

---

## 🔐 Security & Legal

- **Never commit secrets** — Use `.env` (ignored by git)
- **Admin token** — Keep `ADMIN_API_KEY` private
- **Scraper compliance** — Document site ToS in `docs/legal.md`
- **Resume data** — Treat as PII; encrypt at rest in production

---

## 📈 Development Roadmap

See **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** for detailed breakdown:

| Phase | Feature | Weeks | Status |
|-------|---------|-------|--------|
| 1 | Job Portal Spiders | 2 | 🚧 Ready to start |
| 2 | Additional Spiders | 1 | 🚧 |
| 3 | Resume Upload & Skills | 2 | 🚧 |
| 4 | Embeddings & Recommendations | 1 | 🚧 |
| 5 | JWT Auth & Login | 1 | 🚧 |
| 6 | Job Dashboard UI | 1 | 🚧 |
| 7 | Email Notifications | 1 | 🚧 |
| 8 | Security Hardening | 1 | 🚧 |
| 9 | Kubernetes Deployment | 1 | 🚧 |

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b dev/feature-name`
2. Follow patterns in [.github/copilot-instructions.md](./.github/copilot-instructions.md)
3. Write tests for new features
4. Open a PR with description of changes
5. Do NOT commit directly to main

---

## 📞 Support

### Documentation
- **Architecture:** See `docs/` directory
- **API Docs:** http://localhost:8000/docs (when running locally)
- **Monitoring:** See Grafana dashboards at http://localhost:3000

### Common Issues
See [QUICK_START.md](./QUICK_START.md) troubleshooting section

---

## 📄 License

[To be determined]

---

**Starting development? Read [QUICK_START.md](./QUICK_START.md) first!** 🚀
