# Routes package
# Health router: Fully working, no external dependencies
# Other routers: Have dependencies (DB, Redis, MinIO) that may not be initialized
# Loading them selectively to handle graceful degradation

from . import health

# Try to import additional routers; if any fail, log warning and continue with just health
try:
    from . import users
except Exception as e:
    import logging
    logging.warning(f"Failed to import users router: {e}")

try:
    from . import jobs
except Exception as e:
    import logging
    logging.warning(f"Failed to import jobs router: {e}")

try:
    from . import resumes
except Exception as e:
    import logging
    logging.warning(f"Failed to import resumes router: {e}")

try:
    from . import recommendations
except Exception as e:
    import logging
    logging.warning(f"Failed to import recommendations router: {e}")

try:
    from . import admin
except Exception as e:
    import logging
    logging.warning(f"Failed to import admin router: {e}")
