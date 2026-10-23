"""
Daily email digest scheduler — sends personalised job digests at 7:00 AM IST.

Each user with an uploaded resume receives:
  - Top-N matching jobs (by skill overlap, freshness)
  - Match score, company, location, salary, apply link
  - Only jobs not already sent to that user

Timezone: Asia/Kolkata (UTC+5:30)
Schedule:  07:00 IST every day
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

DIGEST_HOUR = 7
DIGEST_MINUTE = 0
DIGEST_TIMEZONE = "Asia/Kolkata"
MAX_JOBS_PER_DIGEST = 10
MIN_MATCH_SCORE = 0.3  # only send jobs above this threshold


class DailyEmailScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=DIGEST_TIMEZONE)

    def start(self):
        if self.scheduler.running:
            return
        self.scheduler.add_job(
            self._run_sync,
            CronTrigger(
                hour=DIGEST_HOUR,
                minute=DIGEST_MINUTE,
                timezone=DIGEST_TIMEZONE,
            ),
            id="daily_email_digest",
            name=f"Daily job digest at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d} {DIGEST_TIMEZONE}",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        logger.info(
            f"EMAIL SCHEDULER: Started — daily digest at "
            f"{DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d} {DIGEST_TIMEZONE}"
        )

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("EMAIL SCHEDULER: Stopped")

    def _run_sync(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run_digest())
        except Exception as e:
            logger.error(f"EMAIL SCHEDULER: Digest run failed — {e}")
        finally:
            loop.close()

    async def _run_digest(self):
        from app.db.session import AsyncSessionLocal
        from app.models.models import User, Resume, Job as JobModel, EmailLog
        from app.services.email_service import EmailService
        from app.services.skill_extractor import extract_skills_from_text
        import json
        from sqlalchemy import select

        logger.info("EMAIL SCHEDULER: Starting digest run…")
        email_svc = EmailService()

        async with AsyncSessionLocal() as db:
            users_result = await db.execute(
                select(User).where(User.is_active == True)
            )
            users = users_result.scalars().all()
            logger.info(f"EMAIL SCHEDULER: Processing {len(users)} active users")

            for user in users:
                try:
                    await self._send_user_digest(db, user, email_svc)
                except Exception as e:
                    logger.error(f"EMAIL SCHEDULER: Failed for {user.email} — {e}")

        logger.info("EMAIL SCHEDULER: Digest run complete")

    async def _send_user_digest(self, db, user, email_svc):
        from app.models.models import Resume, Job as JobModel, EmailLog, UserProfile
        from app.services.skill_extractor import extract_skills_from_text
        import json
        from sqlalchemy import select

        # Find user's most recent resume
        resume_result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user.id)
            .order_by(Resume.created_at.desc())
        )
        resume = resume_result.scalars().first()

        # Extract skills (from resume or from profile)
        resume_skills: list = []
        if resume and resume.parsed_text:
            resume_skills = extract_skills_from_text(resume.parsed_text)

        # Load user profile preferences
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalars().first()
        target_roles: list = []
        preferred_locations: list = []
        work_mode: str = "any"
        if profile:
            try:
                target_roles = json.loads(profile.target_roles or "[]")
            except Exception:
                pass
            try:
                preferred_locations = json.loads(profile.preferred_locations or "[]")
            except Exception:
                pass
            if profile.skills:
                try:
                    profile_skills = json.loads(profile.skills)
                    resume_skills = list(set(resume_skills) | set(profile_skills))
                except Exception:
                    pass
            work_mode = profile.work_mode or "any"

        if not resume_skills and not target_roles:
            return  # Nothing to match against

        # Prevent duplicate same-day digest
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        already_sent_result = await db.execute(
            select(EmailLog.subject)
            .where(
                EmailLog.user_id == user.id,
                EmailLog.email_type == "digest",
                EmailLog.created_at >= yesterday,
                EmailLog.status == "sent",
            )
        )
        if already_sent_result.scalars().first():
            logger.info(f"EMAIL SCHEDULER: Digest already sent today to {user.email}")
            return

        # Fetch recent jobs (last 7 days), fall back to latest 100
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        jobs_result = await db.execute(
            select(JobModel)
            .where(JobModel.posted_at >= week_ago)
            .order_by(JobModel.posted_at.desc())
            .limit(300)
        )
        jobs = jobs_result.scalars().all()
        if not jobs:
            jobs_result = await db.execute(
                select(JobModel).order_by(JobModel.posted_at.desc()).limit(100)
            )
            jobs = jobs_result.scalars().all()
        if not jobs:
            return

        # Score jobs: skill overlap + role title match + location match
        scored = []
        resume_skills_lower = {s.lower() for s in resume_skills}
        target_roles_lower = [r.lower() for r in target_roles]
        preferred_locations_lower = [l.lower() for l in preferred_locations]

        for job in jobs:
            # Skip remote-only jobs if work_mode is onsite/hybrid
            if work_mode in ("onsite", "hybrid"):
                loc = (job.location or "").lower()
                if loc in ("remote", "worldwide", "anywhere") or job.job_type == "Remote":
                    continue

            desc = ((job.title or "") + " " + (job.description or "")).lower()

            # Skill overlap score (0–1)
            skill_matches = sum(1 for s in resume_skills_lower if s in desc)
            skill_score = skill_matches / max(len(resume_skills_lower), 1) if resume_skills_lower else 0

            # Role title match bonus (0 or 0.3)
            role_score = 0.3 if any(r in (job.title or "").lower() for r in target_roles_lower) else 0

            # Location match bonus (0 or 0.2)
            job_loc = (job.location or "").lower()
            loc_score = 0.2 if any(l in job_loc for l in preferred_locations_lower) else 0

            combined = skill_score + role_score + loc_score
            if combined > 0:
                scored.append((combined, job))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [(sc, j) for sc, j in scored if sc >= MIN_MATCH_SCORE][:MAX_JOBS_PER_DIGEST]

        if not top:
            logger.info(f"EMAIL SCHEDULER: No matching jobs for {user.email}")
            return

        # Send digest email
        subject = f"🎯 Your Daily Job Digest — {len(top)} matches"
        html = _build_digest_html(top, resume_skills)
        text = _build_digest_text(top)

        success = await email_svc.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html,
            plain_text=text,
        )

        # Log result
        log = EmailLog(
            user_id=user.id,
            email_type="digest",
            recipient_email=user.email,
            subject=subject,
            status="sent" if success else "failed",
            sent_at=datetime.now(timezone.utc) if success else None,
        )
        db.add(log)
        await db.commit()

        if success:
            logger.info(f"EMAIL SCHEDULER: Digest sent to {user.email} ({len(top)} jobs)")
        else:
            logger.warning(f"EMAIL SCHEDULER: Failed to send digest to {user.email}")


def _build_digest_html(top_jobs: list, resume_skills: list) -> str:
    rows = ""
    for score, job in top_jobs:
        pct = int(score * 100)
        color = "#22c55e" if pct >= 60 else "#f59e0b"
        apply_btn = (
            f'<a href="{job.apply_url}" style="color:#6366f1;text-decoration:none;">Apply →</a>'
            if job.apply_url else "N/A"
        )
        salary = f"<td style='padding:8px;'>{job.salary_range}</td>" if job.salary_range else "<td></td>"
        rows += f"""
        <tr style='border-bottom:1px solid #e5e7eb;'>
            <td style='padding:8px;'><strong>{job.title}</strong><br>
                <span style='color:#6b7280;font-size:12px;'>{job.company_name or ''}</span></td>
            <td style='padding:8px;color:#374151;'>{job.location or 'Remote'}</td>
            {salary}
            <td style='padding:8px;text-align:center;'>
                <span style='background:{color};color:white;padding:3px 8px;border-radius:12px;font-size:12px;'>{pct}%</span>
            </td>
            <td style='padding:8px;'>{apply_btn}</td>
        </tr>"""

    skills_str = ", ".join(resume_skills[:12])
    return f"""<!DOCTYPE html>
<html>
<body style='font-family:sans-serif;color:#111827;max-width:700px;margin:0 auto;padding:24px;'>
  <h1 style='color:#4f46e5;'>🎯 Your Daily Job Digest</h1>
  <p>Based on your resume skills: <em>{skills_str}</em></p>
  <table style='width:100%;border-collapse:collapse;'>
    <thead>
      <tr style='background:#f3f4f6;'>
        <th style='padding:8px;text-align:left;'>Role</th>
        <th style='padding:8px;text-align:left;'>Location</th>
        <th style='padding:8px;text-align:left;'>Salary</th>
        <th style='padding:8px;text-align:center;'>Match</th>
        <th style='padding:8px;text-align:left;'>Apply</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <hr style='margin:24px 0;border:none;border-top:1px solid #e5e7eb;'>
  <p style='color:#6b7280;font-size:12px;'>
    AutoIntern · You are receiving this because you have an account with a resume.<br>
  </p>
</body>
</html>"""


def _build_digest_text(top_jobs: list) -> str:
    lines = ["Your Daily Job Digest\n", "=" * 40]
    for score, job in top_jobs:
        pct = int(score * 100)
        lines.append(f"\n{job.title} @ {job.company_name or 'Unknown'}")
        lines.append(f"  Location : {job.location or 'Remote'}")
        if job.salary_range:
            lines.append(f"  Salary   : {job.salary_range}")
        lines.append(f"  Match    : {pct}%")
        if job.apply_url:
            lines.append(f"  Apply    : {job.apply_url}")
    lines.append("\n\nAutoIntern — AI-powered job search")
    return "\n".join(lines)


def get_scheduler() -> DailyEmailScheduler:
    return DailyEmailScheduler()
