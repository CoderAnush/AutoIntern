# AutoIntern — Security Audit

**Date**: 2026-10-23  
**Auditor**: Phase 8 / Phase 9 QA pass  
**Scope**: Backend API, authentication, data isolation, secrets management, frontend  

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 1 | FIXED |
| High | 2 | FIXED |
| Medium | 2 | FIXED |
| Low | 3 | DOCUMENTED / ACCEPTED |
| Info | 4 | PASS |

---

## Critical Findings

### SEC-001: ApplicationOut pydantic v2 syntax — 500 on GET /api/applications/

**Severity**: Critical  
**Status**: FIXED  
**File**: `services/api/app/schemas/application.py`

**Description**: `ApplicationOut.Config` used pydantic v2's `from_attributes = True` instead of pydantic v1's `orm_mode = True`. Because the codebase pins pydantic 1.10.x, this caused every call to `GET /api/applications/` to fail with a 500 `ValidationError: value is not a valid dict`. Users could not read their application history.

**Reproduction**:
```
POST /api/auth/login → get token
GET /api/applications/ with Authorization: Bearer <token>
→ 500 Internal Server Error
```

**Fix applied**:
```python
# Before (broken — pydantic v2 syntax):
class Config:
    from_attributes = True

# After (correct — pydantic v1 syntax):
class Config:
    orm_mode = True
```

**Retest**: `test_multiuser_isolation.py::test_users_cannot_see_each_others_applications` — PASS  
**Remaining risk**: None. Fix is straightforward and confirmed by test.

---

## High Findings

### SEC-002: Missing `preferred_job_types` / `min_salary` — silent data loss

**Severity**: High  
**Status**: FIXED  
**File**: `services/api/app/routes/preferences.py`, `services/api/app/models/models.py`

**Description**: The frontend settings page sends `preferred_job_types` (array) and `min_salary` (string) to `PUT /api/preferences/`, but these fields were not present in `PreferencesIn`, `PreferencesOut`, or the `UserProfile` database model. The backend silently ignored them. Users' job type preferences and salary floor were never saved, causing incorrect job matching.

**Fix applied**: Added `preferred_job_types` column to `UserProfile`; added both fields to all schema classes and the upsert handler.

**Remaining risk**: PostgreSQL production database requires an Alembic migration to add the new column before deploying. Without it, the column does not exist and inserts will fail.

**Migration required**:
```sql
ALTER TABLE user_profiles ADD COLUMN preferred_job_types TEXT;
```
Or run: `alembic revision --autogenerate -m "add preferred_job_types" && alembic upgrade head`

---

### SEC-003: Cover letter endpoint used unresolved request object

**Severity**: High  
**Status**: FIXED  
**File**: `services/api/app/routes/ai_features.py`

**Description**: `POST /api/ai/cover-letter` resolved job title and company name from DB into local variables, but the Gemini prompt and the template fallback still referenced the original (potentially None) `req` fields instead of the resolved values. A request with `job_id` pointing to a real job but no inline `job_title`/`company_name` would send an empty or None prompt to Gemini, potentially generating a cover letter with no job title or company.

**Fix applied**: Updated Gemini prompt construction and `_template_cover_letter()` call to use the resolved `job_title`, `company_name`, `job_description`, and `resume_summary` variables.

**Remaining risk**: None for logic correctness. Gemini API key still optional; template fallback is used when key absent.

---

## Medium Findings

### SEC-004: Test suite crashed when sentence-transformers absent

**Severity**: Medium (test infrastructure)  
**Status**: FIXED  
**File**: `services/api/tests/test_embeddings.py`

**Description**: `test_embeddings.py` imported `sentence_transformers` at module level without a guard, causing the entire test suite to fail with `ModuleNotFoundError` when run in a CI environment without ML dependencies.

**Fix applied**: Added `pytest.importorskip("sentence_transformers", reason="...")` at the top of the file. Tests now show as SKIPPED with a clear reason rather than crashing.

---

### SEC-005: Missing `conftest.py` — env vars set too late

**Severity**: Medium (test isolation)  
**Status**: FIXED  
**File**: `services/api/tests/conftest.py`

**Description**: Without a `conftest.py`, each test file had to set `DATABASE_URL` itself. If a test file earlier in the collection order imported app modules first (without setting the env var), `UUIDType` would be set to `PostgresUUID` for the entire session, causing SQLite-incompatible schema for all subsequent tests.

**Fix applied**: Created `tests/conftest.py` that sets `DATABASE_URL`, `SECRET_KEY`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, and `REDIS_URL` before any imports.

---

## Low / Accepted Risks

### SEC-006: Alembic migration not generated for new columns

**Severity**: Low  
**Status**: Documented — action required before production deploy

New columns added in Phase 8 and Phase 9:
- `users`: `failed_login_attempts`, `locked_until`, `last_login_attempt`, `notify_on_new_jobs`, `notify_on_resume_upload`, `notify_on_password_change`, `weekly_digest`, `email_frequency`
- `user_profiles`: (entire table — new in Phase 8); `preferred_job_types` (Phase 9)
- `saved_jobs`: (entire table — new in Phase 8)
- `request_logs`: (entire table — new in Phase 8)
- `email_logs`: (entire table — new in Phase 8)

Development uses `create_all()` which handles these automatically. **Production PostgreSQL requires `alembic upgrade head` before deploying.**

**Action**: Run `alembic revision --autogenerate` and review the generated migration before deploying to production.

---

### SEC-007: Playwright e2e test TypeScript errors

**Severity**: Low  
**Status**: Documented — test infrastructure only

`e2e/auth.spec.ts` and `e2e/integration.spec.ts` use deprecated/incorrect Playwright API. TypeScript reports 4 errors. These files test the app but are not application code; the build succeeds and all 12 pages compile cleanly.

**Action**: Update Playwright API usage in e2e test files before running browser automation in CI.

---

### SEC-008: Redis optional — rate limiter silently disabled

**Severity**: Low  
**Status**: Accepted (by design)

When `REDIS_URL` is not set or Redis is unavailable, the rate limiter logs a warning and allows all requests through. This is intentional for development/solo-use but should be enabled for public deployment.

**Action**: Set `REDIS_URL` in production. Test with `redis-cli ping` before deploy.

---

## Information / Verified Controls

### SEC-INFO-001: Passwords never stored in plaintext

**Status**: VERIFIED  
Passwords are hashed with argon2/bcrypt via passlib. `test_auth.py` confirms raw passwords are never stored. Hash verification tested for both correct and incorrect passwords.

### SEC-INFO-002: JWT tokens include expiry and type claim

**Status**: VERIFIED  
All tokens have `exp`, `type` (access/refresh), and `user_id` claims. Wrong secret key, expired tokens, and type mismatches all raise `JWTError` as verified by `test_auth.py`.

### SEC-INFO-003: Multi-user data isolation enforced at query level

**Status**: VERIFIED  
All database queries include `WHERE user_id = <current_user_id>`. Cross-user access to resumes, applications, and email logs tested and confirmed to return 404 or empty list.

### SEC-INFO-004: `.env` file not committed

**Status**: VERIFIED  
`.gitignore` at repo root includes `.env`. No `.env` files exist in the repository. All secrets are read from environment variables via `python-dotenv` for local dev and from the host environment in production.

---

## Secrets Management

| Secret | Dev | Prod |
|--------|-----|------|
| `SECRET_KEY` | `.env` (not committed) | Environment variable |
| `DATABASE_URL` | `.env` (not committed) | Environment variable |
| `GEMINI_API_KEY` | `.env` (optional) | Environment variable |
| `SMTP_PASS` | `.env` (not committed) | Environment variable |
| `REDIS_URL` | `.env` (optional) | Environment variable |

**No secrets appear in**:
- Source code
- Committed files
- Log output
- API responses
- Test output

---

## Remaining Actions Before Public Launch

1. Generate and test Alembic migration for all new tables/columns
2. Enable Redis for rate limiting in production
3. Set strong `SECRET_KEY` (≥ 32 random bytes) in production environment
4. Enable HTTPS (TLS termination at reverse proxy or platform level)
5. Set `SMTP_PASS` and verify email delivery end-to-end
6. Fix Playwright e2e TypeScript errors and run browser tests against staging
