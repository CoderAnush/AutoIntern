def test_db_session_importable():
    # sanity-check: the db session module should import and expose an engine
    from app.db import session

    assert hasattr(session, "engine")
    assert hasattr(session, "AsyncSessionLocal")
