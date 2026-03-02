import asyncio, logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.email_service import EmailService
from app.db.session import SessionLocal
from app.models.models import User, Resume

logger = logging.getLogger(__name__)

class DailyEmailScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.email_service = EmailService()
        
    def start(self):
        if self.scheduler.running:
            return
        self.scheduler.add_job(
            self.send_daily_emails,
            CronTrigger(hour=6, minute=0),
            id='daily_job_emails',
            name='Send daily job recommendations',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("EMAIL SCHEDULER: Started - Daily emails at 6:00 AM")
    
    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("EMAIL SCHEDULER: Stopped")
    
    async def send_daily_emails(self):
        logger.info("EMAIL SCHEDULER: Starting daily email job...")
        db = SessionLocal()
        try:
            users = db.query(User).all()
            for user in users:
                try:
                    resume = db.query(Resume).filter(Resume.user_id == user.id).first()
                    if not resume:
                        continue
                    
                    subject = "Daily Job Recommendations - AutoIntern"
                    html = f"<html><body><h1>Hello {user.name}</h1><p>Here are your top job recommendations for today based on your resume.</p><p>Visit AutoIntern to see more details and apply!</p></body></html>"
                    text = f"Hello {user.name},\n\nHere are your top job recommendations for today.\n\nVisit AutoIntern to apply!"
                    
                    await self.email_service.send_email(
                        to_email=user.email,
                        subject=subject,
                        html_content=html,
                        plain_text=text
                    )
                    logger.info(f"EMAIL SENT: {user.email}")
                except Exception as e:
                    logger.error(f"EMAIL ERROR: {user.email} - {e}")
        finally:
            db.close()
        logger.info("EMAIL SCHEDULER: Daily job completed")

def get_scheduler():
    return DailyEmailScheduler()
