Integration testing notes

- These tests require the dev stack to be running (Postgres via `docker compose up`).
- To run integration tests locally:
  - `cp .env.example .env`
  - `docker compose up --build -d`
  - `cd services/api`
  - `pip install -r requirements.txt`
  - `pytest -q` (tests that need DB will be skipped if DB unreachable)

- CI runs the same steps in `.github/workflows/ci.yml` and will apply Alembic migrations before executing tests.
