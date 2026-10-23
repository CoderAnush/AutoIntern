# AutoIntern — QA Test Plan

**Revision**: Phase 8 / Phase 9  
**Date**: 2026-10-23  
**Environment**: Windows 11, Python 3.12.10, Node 24, SQLite (test) / PostgreSQL (prod)

---

## 1. System Components Under Test

| Component | Tech |
|-----------|------|
| Backend API | FastAPI 0.99.1 + Pydantic 1.10.26 |
| Database | SQLAlchemy 2.0 async, SQLite (dev/test), PostgreSQL (prod) |
| Authentication | JWT (python-jose), bcrypt/argon2 password hashing |
| Job sources | Greenhouse API, Lever API, RemoteOK JSON |
| Email delivery | aiosmtplib async SMTP |
| Scheduler | APScheduler BackgroundScheduler |
| AI features | Google Gemini 1.5 Flash (optional); template fallback |
| Frontend | Next.js 14, React 18, TypeScript |

---

## 2. Test Scope

### In scope
- Authentication (register, login, JWT)
- Multi-user data isolation (IDOR prevention)
- User preferences / profile contract
- Saved jobs CRUD
- Applications CRUD
- Email logs access
- AI cover letter / interview prep endpoints
- Scheduler configuration and startup
- Job source adapter syntax
- Frontend build (TypeScript/Next.js compilation)
- Database model syntax and schema correctness

### Out of scope (environment constraints)
- Live job scraping (rate limits, external network dependency)
- Live SMTP delivery (no SMTP server in test environment)
- Gemini AI (requires API key)
- PostgreSQL-specific migration tests (no PostgreSQL instance)
- Browser E2E tests (Playwright — no headed browser in CI)
- sentence-transformers / FAISS embeddings (heavy ML deps not installed)

---

## 3. Test Environment

### Backend
```
Python: 3.12.10 (system, AppData\Local\Programs\Python\Python312)
Packages: pip install --user (no venv; AppData\Local\Programs blocks new .exe)
Database: sqlite+aiosqlite:///:memory: (tests), autointern.db (dev)
Test runner: pytest 7.4.3 + pytest-asyncio 0.21.1
Working dir: services/api
```

**Important**: Windows Application Control blocks `.pyd` DLLs in non-system paths. The system Python at `AppData\Local\Programs\Python\Python312` is trusted. Do NOT use `venv` on the Desktop/OneDrive path.

**Command to install deps:**
```
python -m pip install --user --no-binary pydantic "pydantic[email]<2.0,>=1.10.21" fastapi==0.99.1 uvicorn python-multipart SQLAlchemy==2.0.23 aiosqlite==0.19.0 alembic==1.12.1 "python-jose[cryptography]==3.3.0" "passlib[argon2]==1.7.4" httpx==0.25.2 pytest==7.4.3 pytest-asyncio==0.21.1 pytest-mock==3.12.0 pdfplumber==0.10.3 aiosmtplib==3.0.1 apscheduler==3.10.4 pytz==2023.3 python-dotenv==1.0.0 email-validator argon2-cffi redis numpy
```

### Frontend
```
Node: 24.22.0
npm: 11.19.1
Working dir: services/web/apps/dashboard
```

---

## 4. Test Categories and Commands

### 4A. Backend unit + integration tests
```
cd services/api
python -m pytest tests/ --ignore=tests/test_jobs_integration.py -v
```
Ignores `test_jobs_integration.py` (needs `psycopg2` for PostgreSQL synchronous engine).

### 4B. Multi-user isolation tests
```
cd services/api
python -m pytest tests/test_multiuser_isolation.py -v
```
These use SQLite in-memory, mock all external services, take ~2–3 minutes.

### 4C. Static syntax check
```
cd services/api
python -m compileall -q app
```

### 4D. Frontend TypeScript / build
```
cd services/web/apps/dashboard
npm install
npx next build
npx tsc --noEmit   # 4 errors in e2e/ only — app code is clean
```

---

## 5. Unit Tests

| File | Tests | Coverage |
|------|-------|----------|
| test_auth.py | 30 | Password validation, hashing, JWT create/decode/verify |
| test_auth_integration.py | 20 | Full auth pipeline, refresh, session invalidation |
| test_security.py | 36 | Rate limiter, account lockout, security headers |
| test_emails.py | ~15 | Email queue, retry logic |
| test_resumes.py | ~10 | Resume parsing, skill extraction |
| test_job_dedup.py | ~8 | MD5 dedup logic |
| test_job_sources.py | ~5 | Adapter parsing |
| test_db_import.py | 1 | DB session module importable |
| test_embeddings.py | 11 (SKIPPED) | sentence-transformers not installed |

---

## 6. Integration Tests

| File | Tests | Notes |
|------|-------|-------|
| test_multiuser_isolation.py | 6 | Full HTTP via HTTPX + SQLite in-memory |
| test_jobs_integration.py | BLOCKED | Needs psycopg2 (PostgreSQL sync engine) |

---

## 7. API Contract Tests

| Endpoint | Frontend field | Backend field | Status |
|----------|---------------|---------------|--------|
| GET /api/preferences/ | `preferred_job_types` | `preferred_job_types` | FIXED |
| GET /api/preferences/ | `min_salary` | `min_salary` (derived from salary_min_lpa) | FIXED |
| GET /api/saved-jobs/ | `{id, job_id, job_title, ...}` | SavedJobItem schema | OK |
| POST /api/ai/cover-letter | `job_id`, `resume_id` | DB lookup + fallback | OK |
| GET /api/applications/ | `ApplicationOut` | pydantic v1 orm_mode | FIXED |

---

## 8. Security Tests

Covered in `test_security.py` and `test_auth.py`:
- Password minimum length, complexity requirements
- Passwords are never stored raw (hashed with argon2/bcrypt)
- JWT tokens include expiry, type claim, user_id
- Wrong secret key rejected
- Rate limiter (Redis-backed, graceful degradation if Redis unavailable)
- Account lockout after N failed attempts
- Security headers (X-Content-Type, X-Frame-Options, HSTS, CSP)

---

## 9. Database Tests

- Schema: `python -m compileall -q app/models` — PASS
- In-memory SQLite: test_multiuser_isolation.py creates and migrates tables — PASS
- `UserProfile` and `SavedJob` models: added in Phase 8; require Alembic migration for PostgreSQL prod
- `preferred_job_types` column: added to `UserProfile` in Phase 9

---

## 10. Test Data Strategy

- In-memory SQLite for isolation tests (no leftover state between runs)
- No live external services used in tests
- No real SMTP delivery; rate limiter errors are swallowed gracefully
- `conftest.py` sets safe env vars before any imports

---

## 11. Known Limitations

1. **No live job-source validation** — adapters verified by `py_compile` only; live API responses not tested in this run
2. **No PostgreSQL migration test** — `create_all` used in dev; prod needs `alembic upgrade head`
3. **No browser E2E test** — Playwright installed in package.json but not runnable headlessly without a display server; 4 TypeScript errors in e2e spec files (wrong Playwright API usage)
4. **No SMTP delivery test** — SMTP server not available; email routes return errors that are gracefully logged
5. **sentence-transformers tests SKIPPED** — requires ~2 GB download; not suitable for CI without caching
