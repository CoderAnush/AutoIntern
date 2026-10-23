# AutoIntern — Implementation Audit

**Date**: 2026-10-23  
**Auditor**: Phase 8 verification pass (Claude Sonnet 4.6)  
**Scope**: All backend services, API routes, models, schedulers, job sources

---

## 1. Verified Features

### Authentication & Users
| Feature | Status | Notes |
|---------|--------|-------|
| `POST /api/auth/register` | ✅ Implemented | bcrypt password hashing |
| `POST /api/auth/login` | ✅ Implemented | JWT access token issued |
| `GET /api/auth/me` | ✅ Implemented | Returns current user info |
| JWT auth middleware | ✅ Implemented | `get_current_user` dependency |
| Multi-user isolation | ✅ Implemented | All queries scoped by `user_id` |

### Resumes
| Feature | Status | Notes |
|---------|--------|-------|
| `POST /api/resumes/upload` | ✅ Implemented | PDF upload + text extraction |
| `GET /api/resumes` | ✅ Implemented | Returns user's resumes only |
| `DELETE /api/resumes/{id}` | ✅ Implemented | User-scoped delete |

### Jobs
| Feature | Status | Notes |
|---------|--------|-------|
| `GET /api/jobs` | ✅ Implemented | Paginated, filterable |
| `POST /api/admin/scrape` | ✅ Implemented | Trigger manual scrape |
| MD5 deduplication | ✅ Implemented | `title+company+location` hash |
| Job scheduler (hourly) | ✅ Implemented | `DailyJobScheduler`, runs at `:00` |

### Applications
| Feature | Status | Notes |
|---------|--------|-------|
| `POST /api/applications` | ✅ Implemented | User-scoped |
| `GET /api/applications` | ✅ Implemented | User-scoped |
| `PUT /api/applications/{id}` | ✅ Implemented | |
| `DELETE /api/applications/{id}` | ✅ Implemented | |

### User Preferences (NEW — Phase 8)
| Feature | Status | Notes |
|---------|--------|-------|
| `UserProfile` DB model | ✅ Implemented | `services/api/app/models/models.py` |
| `GET /api/preferences/` | ✅ Implemented | Returns profile or defaults |
| `PUT /api/preferences/` | ✅ Implemented | Upsert with validation |
| Default initial preferences | ✅ Implemented | See section 3 below |

### Saved Jobs (NEW — Phase 8)
| Feature | Status | Notes |
|---------|--------|-------|
| `SavedJob` DB model | ✅ Implemented | `services/api/app/models/models.py` |
| `GET /api/saved-jobs/` | ✅ Implemented | JOIN with jobs table |
| `POST /api/saved-jobs/{job_id}` | ✅ Implemented | Idempotent bookmark |
| `DELETE /api/saved-jobs/{job_id}` | ✅ Implemented | Returns 204 |

### Email System
| Feature | Status | Notes |
|---------|--------|-------|
| `GET /api/emails/logs` | ✅ Implemented | User-scoped |
| `POST /api/emails/test` | ✅ Implemented | Send test email |
| `POST /api/emails/subscribe` | ✅ Implemented | Enable digest |
| `POST /api/emails/unsubscribe` | ✅ Implemented | Disable digest |
| Daily digest scheduler | ✅ Implemented | 07:00 IST, `Asia/Kolkata` |
| Profile-aware scoring | ✅ Implemented | Skill + role + location scoring |
| Dedup (no same-day repeat) | ✅ Implemented | Checks `EmailLog` before sending |

### AI Features (NEW — Phase 8)
| Feature | Status | Notes |
|---------|--------|-------|
| `POST /api/ai/cover-letter` | ✅ Implemented | Gemini or template fallback |
| `POST /api/ai/interview-prep` | ✅ Implemented | Gemini or template fallback |
| `job_id` DB lookup | ✅ Implemented | Resolves title/company from DB |
| `resume_id` DB lookup | ✅ Implemented | Resolves summary from DB |
| GEMINI_API_KEY server-side only | ✅ Implemented | Never sent to browser |

### Scheduler Status Endpoints (NEW — Phase 8)
| Feature | Status | Notes |
|---------|--------|-------|
| `GET /api/scheduler/status` | ✅ Implemented | Returns both schedulers' next fire times |
| `POST /api/scheduler/trigger` | ✅ Implemented | Manual scrape trigger |

---

## 2. Defects Fixed This Session

| # | File | Bug | Fix Applied |
|---|------|-----|-------------|
| 1 | `app/routes/emails.py` | `from app.core.database import get_session` — module does not exist | Changed to `from app.db.session import get_db as get_session`; removed unused `selectinload` import |
| 2 | `app/main.py` | `emails` router was never mounted | Added `app.include_router(emails.router, prefix="/api")` |
| 3 | `app/main.py` | `preferences`, `saved_jobs`, `ai_features` routers missing | Added all three with correct prefixes |
| 4 | `app/services/job_sources.py` | PagerDuty listed under Lever (wrong ATS) | Moved PagerDuty to Greenhouse adapter; removed stale `retool` Lever entry |
| 5 | `app/routes/saved_jobs.py` | Endpoint did not exist; frontend called `GET /api/saved-jobs/` | Created full route + `SavedJob` model |
| 6 | `app/routes/preferences.py` | Endpoint did not exist; frontend called `GET /api/preferences/` | Created full route + `UserProfile` model |
| 7 | `app/routes/ai_features.py` | Cover-letter route only accepted raw `job_title`/`company_name`; frontend sends `job_id` | Added `job_id`/`resume_id` optional fields with DB lookup; added `job_title`/`company_name` to response |
| 8 | `app/routes/ai_features.py` | Post-DB-lookup, rest of function still used `req` (pre-resolved) | Updated Gemini prompt and template call to use resolved local variables |

---

## 3. Initial User Profile (Defaults)

When a user has no saved profile, `GET /api/preferences/` returns:

```json
{
  "target_roles": [
    "AI Engineer", "ML Engineer", "Data Scientist",
    "Applied AI Engineer", "Python Developer", "Software Engineer"
  ],
  "preferred_locations": [
    "India", "Bangalore", "Hyderabad", "Mumbai", "Pune", "Chennai"
  ],
  "graduation_year": 2027,
  "experience_level": "fresher",
  "work_mode": "hybrid",
  "salary_min_lpa": 10,
  "open_to_remote": false,
  "skills": []
}
```

These match the spec: graduation 2027, India/hybrid only, ≥₹10 LPA, no fully remote.

---

## 4. Job Sources

### Greenhouse (24 companies, public board API — no auth)
| Company | Token |
|---------|-------|
| Stripe | stripe |
| Airbnb | airbnb |
| Dropbox | dropbox |
| Figma | figma |
| Notion | notion |
| Twilio | twilio |
| HashiCorp | hashicorp |
| Cloudflare | cloudflare |
| GitHub | github |
| Robinhood | robinhood |
| Duolingo | duolingo |
| Brex | brex |
| Plaid | plaid |
| Vercel | vercel |
| Amplitude | amplitude |
| Grammarly | grammarly |
| Canva | canva |
| Confluent | confluent |
| MongoDB | mongodb |
| Databricks | databricks |
| PagerDuty | pagerduty |
| Coinbase | coinbase |
| Benchling | benchling |
| Samsara | samsara |

### Lever (6 companies, public postings API — no auth)
| Company | Token |
|---------|-------|
| Airtable | airtable |
| Linear | linear |
| Netlify | netlify |
| Segment | segment |
| LaunchDarkly | launchdarkly |
| Instacart | instacart |

### Other
| Source | Adapter | Notes |
|--------|---------|-------|
| RemoteOK | remoteok | Public JSON API; capped at 50 per run |

**Total sources: 31** (24 Greenhouse + 6 Lever + 1 RemoteOK)

---

## 5. Personalized Digest Scoring (Daily Email)

Each job is scored against the user's profile before sending:

```
score = skill_score + role_score + loc_score
```

- **skill_score** (0–1): fraction of resume/profile skills found in job title+description
- **role_score** (0 or +0.3): if any `target_roles` keyword appears in the job title
- **loc_score** (0 or +0.2): if any `preferred_locations` appears in the job location

Jobs with `score < 0.3` are excluded. Remote-only jobs (location: "remote", "worldwide", "anywhere", or `job_type = "Remote"`) are skipped when `work_mode` is `onsite` or `hybrid`.

Top 10 scoring jobs are sent per digest. Same-day duplicates are prevented by checking `EmailLog` before sending.

---

## 6. Multi-User Isolation

**Architecture**: Every DB query that reads or writes user data includes a `WHERE user_id = <current_user_id>` clause. The `current_user` is extracted from the JWT token by `get_current_user` (FastAPI dependency), never from query parameters.

**Test file**: `services/api/tests/test_multiuser_isolation.py`

Tests cover:
- Resume isolation: User A cannot see User B's resumes
- Application isolation: User A cannot see User B's applications
- Preferences isolation: User A cannot see User B's profile preferences
- Saved-jobs isolation: Saved-jobs list is user-scoped
- Email log isolation: Email log IDs must not overlap between users
- Unauthenticated access: All protected endpoints return 401/403 without token

> **Limitation**: Tests require Python env with `aiosqlite`, `httpx`, `pytest-asyncio`. They were written and syntax-verified but not executed (no Python virtual environment was available in `services/api/`). To run: `pip install pytest pytest-asyncio httpx aiosqlite && pytest tests/test_multiuser_isolation.py -v`

---

## 7. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Async SQLAlchemy URL. Dev default: `sqlite+aiosqlite:///./autointern.db` |
| `SECRET_KEY` | Yes | JWT signing secret (min 32 chars) |
| `SMTP_HOST` | Yes* | SMTP server hostname (*required for email delivery) |
| `SMTP_PORT` | No | Default: 587 |
| `SMTP_USER` | Yes* | SMTP username/email |
| `SMTP_PASS` | Yes* | SMTP password |
| `SMTP_FROM` | No | From address; falls back to `SMTP_USER` |
| `GEMINI_API_KEY` | No | Google Gemini API key; AI routes use template fallback if absent |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `MIGRATE_ON_START` | No | Set to `true` to auto-apply Alembic migrations at startup |
| `REDIS_URL` | No | Optional Redis URL for caching |

**Security**: `.env` files must never be committed. All secrets live in environment variables or a secrets manager.

---

## 8. Scheduler Configuration

### Daily Email Digest
- **Trigger**: CronTrigger `hour=7, minute=0, timezone="Asia/Kolkata"` (07:00 IST)
- **Behavior**: Processes all active users with a resume; scores jobs against profile; sends top 10 matches via SMTP; logs result to `EmailLog`
- **Dedup**: Skips users who already received a digest today
- **Graceful fallback**: Users with no resume and no profile preferences are skipped without error

### Job Scraper
- **Trigger**: Every hour at `:00` (configurable)
- **Behavior**: Fetches all 31 sources concurrently via `httpx.AsyncClient`; deduplicates by MD5 signature; upserts to `jobs` table
- **Startup**: If `jobs` table is empty at startup, triggers an immediate scrape

---

## 9. Known Limitations / Not Implemented

| Item | Status | Notes |
|------|--------|-------|
| `preferred_job_types` preference | Partial | Frontend `settings` page accesses `data.preferred_job_types` and `data.min_salary`; these fall back gracefully to `[]`/`""` but are not stored in `UserProfile` |
| Workday/Ashby adapters | Not implemented | Stubs exist in `job_sources.py`; would require per-company URL configuration |
| Resume skill extraction accuracy | Basic | `extract_skills_from_text` uses keyword matching, not NLP |
| Job scraper rate limiting | None | No per-source rate limiting; relies on API server limits |
| Live test run | Not executed | No virtualenv available during audit; all checks were static (`py_compile`) |
| Alembic migration for new models | Not run | `UserProfile` and `SavedJob` tables created via `Base.metadata.create_all` at startup in dev; for PostgreSQL prod, generate and run a new migration: `alembic revision --autogenerate -m "add_user_profile_saved_jobs"` |

---

## 10. Deployment Notes

1. **Generate an Alembic migration** before first production deploy:
   ```
   alembic revision --autogenerate -m "add_user_profile_saved_jobs"
   alembic upgrade head
   ```

2. **Set all required env vars** in your deployment environment (see section 7).

3. **GEMINI_API_KEY** is optional. Without it, `/api/ai/cover-letter` and `/api/ai/interview-prep` return template-based responses.

4. **SMTP configuration** is required for digest emails. Without it, the scheduler runs but `EmailService.send_email` will log failures silently.

5. **Do not commit `.env` files**. The `.gitignore` should already exclude them.

6. **CORS**: Set `CORS_ORIGINS` to your frontend domain in production. The default dev config allows all origins.
