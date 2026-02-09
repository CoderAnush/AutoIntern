API service (FastAPI)

DB migrations (Alembic):
- Change into `services/api`
- Use the included `alembic.ini`:
  - `alembic -c alembic.ini revision --autogenerate -m "your message"`
  - `alembic -c alembic.ini upgrade head`

Note: the Alembic `env.py` uses `app.models.models:Base` as `target_metadata` so autogeneration should pick up model changes.

Development shortcuts:
- To create DB tables automatically in dev, set `MIGRATE_ON_START=true` (or `migrate_on_start=true`) in `.env` and start the API with that env var set.
