def test_db_session_importable():
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
