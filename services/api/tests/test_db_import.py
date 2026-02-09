def test_db_session_importable():
    # sanity-check: the db session module should import and expose an engine
    # Import using package path relative to repo root
    from services.api.app.db import session

    assert hasattr(session, "engine")
    assert hasattr(session, "AsyncSessionLocal")
