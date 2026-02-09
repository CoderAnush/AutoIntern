# AutoIntern — Copilot Instructions for AI Coding Agents

Goal: Help an AI coding agent be productive immediately in this monorepo by documenting the architecture, developer workflows, important files, and project-specific conventions.

## Quick summary (big picture)
- Monorepo with multiple services under `services/`:
  - `services/api/` — FastAPI application (backend, auth, job endpoints).
  - `services/scraper/` — Scrapy + Playwright spiders, config-driven `BaseJobSpider`.
  - `services/processor/`, `services/ai_engine/`, `services/worker/`, `services/notifications/` — placeholders for processing, embeddings, background workers and notification logic.
  - `frontend/` — React + Tailwind app (placeholder directory).
- Infrastructure deployed locally via `docker-compose.yml` (Postgres, Redis, Elasticsearch, MinIO + service containers).
- Dataflow: scraper -> Redis queue -> processor -> PostgreSQL + Elasticsearch + embeddings store (FAISS/JSONB vectors).

## Must-know files & entry points
- `docker-compose.yml` — local dev stack (ports, service names used in `.env`).
- `.env.example` — canonical env vars (DB, Redis, Elastic, MinIO, JWT secret).
- `services/api/app/main.py` — app startup/shutdown hooks and router registration.
- `services/api/app/routes/` — route modules (example: `health.py`, `users.py`).
- `services/api/app/models/models.py` — SQLAlchemy models; note use of UUID and JSONB (embeddings stored as JSONB vectors currently).
- `services/api/Dockerfile` and `services/api/requirements.txt` — container + dependency details.
- `services/scraper/` — Scrapy project. Key example: `autointern_scraper/spiders/base_spider.py` and `services/scraper/README.md` (run spiders via `scrapy crawl <name>`).
- `scripts/setup_dev.ps1` — helper that copies `.env.example` to `.env` and starts `docker compose`.
- `tests/` — Python tests (e.g., `tests/test_health.py`).
- CI: `.github/workflows/ci.yml` runs minimal tests by installing `services/api/requirements.txt` and running `pytest`.

## Developer workflows (explicit commands)
- Local dev stack: `Copy .env.example to .env` and `docker compose up --build` (or use `scripts/setup_dev.ps1` on Windows PowerShell).
- Run API locally (without Docker): inside `services/api` create venv, `pip install -r requirements.txt`, then `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
- Tests: `pip install -r services/api/requirements.txt` then `pytest -q` from repo root. CI currently only runs `pytest`.
- Scraper: `cd services/scraper` and `scrapy crawl <spider-name>`; Playwright-based spiders require `playwright install` in that environment.
- DB migrations: Alembic is installed in requirements. When changing models add alembic revisions in `migrations/` and run `alembic upgrade head` in the appropriate environment.

## Project-specific conventions & patterns
- Monorepo service layout: put service-specific Dockerfile and `requirements.txt` under `services/<name>/`.
- Use environment variables defined in `.env`; Docker Compose expects the service names from `docker-compose.yml` (e.g., `postgres`, `redis`, `elasticsearch`, `minio`).
- Models use Postgres-specific types (UUID, JSONB). Avoid switching these types unless migrating and adding Alembic migrations.
- Embeddings currently stored as `JSONB` vectors in `embeddings` table: prefer storing serialized floats or delegating to FAISS/Vector DB for large-scale setups.
- Testing pattern: lightweight unit tests under `tests/`. The CI job installs just API requirements and runs `pytest`; ensure tests are self-contained and mock external services (Postgres/Redis/Elastic) or use test containers if needed.

## Integration points & external dependencies
- PostgreSQL — connection via `DATABASE_URL` env var; models in `services/api/app/models/` rely on Postgres features.
- Redis — used as queue and cache; `aioredis` is included in API requirements.
- Elasticsearch — indexing and search; `docker-compose` spins up `elasticsearch:8.x` for local dev.
- MinIO — S3-compatible object storage for resumes and static assets.
- Scrapy/Playwright — dynamic site scraping (Playwright requires `playwright install` and browsers on host/container).

## Spider development checklist (practical pattern)
- Add new site definitions as config files (YAML/JSON) in `services/scraper` (create `sites/` as needed).
- Create a spider that subclasses `BaseJobSpider` and implements `parse` and extraction rules (refer to `base_spider.py`).
- Add robust middleware: proxy rotation, ban detection, rate limiting, retry/backoff.
- Add tests that isolate parsing logic by using sample HTML fixtures and unit tests — do not hit external sites in CI.
- Respect legal constraints: do not add LinkedIn or any site with restrictive TOS without express confirmation. Document such decisions in `docs/legal.md`.

## Coding & PR norms for AI agents
- Always open a draft PR against `main` using a `dev/*` branch (e.g., `dev/init`, `dev/scraper-indeed`) unless instructed otherwise.
- Do not commit or push changes directly to `main` without explicit approval from the repository owner (user requested to be asked before committing any changes).
- Include tests that cover new behavior; update `tests/` and ensure `pytest -q` passes locally.
- When changing DB models, add Alembic migration files under `migrations/` and include guidance in the PR description for applying migrations.
- Keep changes small and focused; each PR should have a clear migration path and roll-back plan.

## Diagnostics & debugging tips
- If tests fail locally due to missing packages, install service-specific requirements (e.g., `pip install -r services/api/requirements.txt`).
- To debug API, use uvicorn `--reload` and attach to `http://localhost:8000/docs` for OpenAPI introspection.
- For scraping, use verbose logs and record sample responses to `tests/fixtures/` to add unit tests for parsing.

## Security & legal notes for AI agents
- Pay attention to the `docs/` directory for legal/ethical guidance. For sites with strict TOS (LinkedIn, Indeed), only add spiders if the owner explicitly approves or an official API is used.
- Never commit secrets to repo. If adding new env vars, update `.env.example` and ensure secrets are stored in a secret manager in production.

## What to update in this file
- Keep this file short and practical. If you (human owner) prefer different branch strategies, linting rules, or CI steps, update this file immediately.

---
If anything in these instructions is unclear or you want more detail on a specific service (e.g., AI engine or processor), tell me which area to expand and I will iterate. ✨
