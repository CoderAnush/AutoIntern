# AutoIntern AI

**AI-powered job-search platform.** Collects real jobs from 30+ company career sites (Greenhouse, Lever, RemoteOK), matches them against your resume, and emails a personalised digest every day at 7:00 AM IST.

---

## Architecture

```
Job Sources (Greenhouse API / Lever API / RemoteOK API)
    ↓  hourly via APScheduler
FastAPI Backend  →  PostgreSQL
    ↓
Matching engine (skill overlap + FAISS / Sentence-BERT)
    ↓
7 AM IST daily digest  →  SMTP email
    ↓
Next.js Dashboard  (auth · jobs · applications · settings)
```

---

## Quick start (Docker)

```bash
# 1. Copy and edit env vars
cp .env.example .env
# Set SECRET_KEY, SMTP credentials, ADMIN_API_KEY

# 2. Start all services
docker compose up --build

# 3. Run database migrations
docker compose exec api alembic -c alembic.ini upgrade head

# 4. Verify
curl http://localhost:8000/health
open http://localhost:8000/docs
open http://localhost:3000          # dashboard
```

---

## Quick start (local dev, no Docker)

### Backend

```bash
cd services/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp ../../.env.example ../../.env    # edit DATABASE_URL → sqlite+aiosqlite:///./autointern.db

uvicorn app.main:app --reload --port 8000
# Database tables are created automatically on first run
```

### Frontend

```bash
cd services/web/apps/dashboard
cp .env.example .env.local          # defaults to http://localhost:8000
npm install
npm run dev                         # opens http://localhost:3000
```

---

## Job sources

30 real companies are configured out of the box using **public, unauthenticated** APIs:

| Adapter    | How it works                                   | Companies (examples)                    |
|------------|------------------------------------------------|-----------------------------------------|
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{token}`   | Stripe, Airbnb, GitHub, Figma, Databricks… |
| Lever      | `api.lever.co/v0/postings/{token}`             | Airtable, Retool, PagerDuty…            |
| RemoteOK   | `remoteok.com/api` (public JSON)               | All remote tech roles                   |

Add new companies by editing `services/api/app/services/job_sources.py` → `COMPANY_REGISTRY`.

---

## Email notifications

- **Schedule:** 7:00 AM IST (Asia/Kolkata) every day
- **Content:** top matching jobs from the last 7 days, scored by skill overlap
- **Requires:** `SMTP_HOST`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD` in `.env`
- **Test:** `POST /api/admin/trigger-scrape` (requires `X-Admin-Token` header)

---

## Directory structure

```
AutoIntern/
├── services/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py         # App startup, scheduler init
│   │   │   ├── routes/         # HTTP endpoints
│   │   │   ├── services/
│   │   │   │   ├── job_sources.py          # Greenhouse / Lever / RemoteOK adapters
│   │   │   │   ├── job_dedup.py            # Deduplication + upsert
│   │   │   │   ├── daily_job_scheduler.py  # Hourly job ingestion
│   │   │   │   ├── daily_email_scheduler.py # 7 AM IST digest
│   │   │   │   ├── recommendation_service.py
│   │   │   │   └── email_service.py
│   │   │   └── models/         # SQLAlchemy ORM models
│   │   └── alembic/            # Database migrations
│   ├── web/apps/dashboard/     # Next.js 14 + TypeScript + Tailwind
│   ├── worker/                 # Redis worker (DLQ processing)
│   └── scraper/                # Scrapy spiders (legacy, kept for future use)
├── infra/                      # Prometheus + Grafana + Alertmanager
├── docker-compose.yml
└── .env.example
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT tokens |
| GET | `/api/jobs/` | List all jobs (paginated) |
| GET | `/api/jobs/search?q=…` | Search jobs |
| POST | `/api/resumes/` | Upload resume (PDF/DOCX/TXT) |
| GET | `/api/recommendations/jobs-for-resume/{id}` | AI-matched jobs |
| GET | `/api/applications/` | Saved/tracked applications |
| POST | `/api/admin/trigger-scrape` | Trigger job ingestion now (admin) |
| POST | `/api/admin/generate-embeddings` | Rebuild FAISS index |

Full docs: `http://localhost:8000/docs`

---

## Environment variables

See `.env.example` for all options with descriptions.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✓ | PostgreSQL or SQLite URL |
| `SECRET_KEY` | ✓ | JWT signing key (min 32 chars) |
| `ADMIN_API_KEY` | ✓ | Protects `/api/admin/*` |
| `SMTP_HOST` | email | SMTP server (e.g. smtp.gmail.com) |
| `SMTP_PORT` | email | Usually 587 |
| `SENDER_EMAIL` | email | From address |
| `SENDER_PASSWORD` | email | App-specific password |
| `REDIS_URL` | workers | Redis for DLQ; optional for API |

---

## Running tests

```bash
cd services/api
pytest -q                           # unit + integration tests
pytest tests/test_auth.py -v        # single file
```

---

## Database migrations

```bash
cd services/api

# Auto-generate from model changes
alembic revision --autogenerate -m "describe change"

# Apply
alembic upgrade head

# Rollback one step
alembic downgrade -1
```
