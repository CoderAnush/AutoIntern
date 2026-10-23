"""Daily job scheduler — collects fresh jobs from real sources every hour."""

import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler_instance = None


class DailyJobScheduler:
    """Runs periodic job ingestion from configured real sources."""

    def __init__(self, hour=None, minute=0):
        self.scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
        self.hour = hour  # None = every hour
        self.minute = minute
        self._running = False

    def start(self):
        if self.scheduler.running:
            return

        if self.hour is None:
            # Run every hour at :minute
            trigger = CronTrigger(minute=self.minute, timezone="Asia/Kolkata")
            desc = f"every hour at :{self.minute:02d}"
        else:
            trigger = CronTrigger(hour=self.hour, minute=self.minute, timezone="Asia/Kolkata")
            desc = f"daily at {self.hour:02d}:{self.minute:02d} IST"

        self.scheduler.add_job(
            self._run_scrape_sync,
            trigger,
            id="job_ingest",
            name=f"Job ingestion ({desc})",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        logger.info(f"JOB SCHEDULER: Started — runs {desc}")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("JOB SCHEDULER: Stopped")

    def run_daily_scrape(self):
        """Trigger an immediate scrape (called from startup or admin endpoint)."""
        self._run_scrape_sync()

    def _run_scrape_sync(self):
        """Synchronous wrapper so APScheduler can call the async scrape."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_scrape())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"JOB SCHEDULER: Scrape failed — {e}")

    async def _run_scrape(self):
        """Fetch jobs from real sources and persist to database."""
        from app.db.session import AsyncSessionLocal
        from app.services.job_sources import collect_all_jobs
        from app.services.job_dedup import upsert_jobs

        logger.info("JOB SCHEDULER: Starting ingestion run...")
        async with AsyncSessionLocal() as db:
            try:
                jobs = await collect_all_jobs()
                if jobs:
                    inserted, skipped = await upsert_jobs(db, jobs)
                    logger.info(
                        f"JOB SCHEDULER: Ingestion complete — {inserted} new, {skipped} duplicate"
                    )
                else:
                    logger.warning("JOB SCHEDULER: No jobs collected this run")
            except Exception as e:
                logger.error(f"JOB SCHEDULER: Ingestion error — {e}")
