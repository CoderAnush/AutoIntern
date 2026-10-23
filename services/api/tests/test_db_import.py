def test_db_session_importable():
    import os
    import pytest
    # Skip test if SQLAlchemy isn't installed (optional dependency in dev)
    pytest.importorskip('sqlalchemy')
    # Requires either psycopg2 (PostgreSQL) or aiosqlite (SQLite) to be importable.
    # Set SQLite URL so the session module doesn't need psycopg2.
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_db_import.db")

    # sanity-check: the db session module should import and expose an engine
    # Ensure services/api is on sys.path so `app` package is importable
    import sys
    import os
    tests_dir = os.path.dirname(__file__)
    services_api_dir = os.path.abspath(os.path.join(tests_dir, '..'))
    if services_api_dir not in sys.path:
        sys.path.insert(0, services_api_dir)

    from app.db import session

    assert hasattr(session, "engine")
    assert hasattr(session, "AsyncSessionLocal")
