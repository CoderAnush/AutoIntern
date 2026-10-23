"""
AI-powered features: cover letter generation and interview prep.
POST /api/ai/cover-letter     → generate a cover letter
POST /api/ai/interview-prep   → generate interview Q&A for a role

Uses Gemini API when GEMINI_API_KEY is set; falls back to template-based
responses so the endpoints never crash in dev.

SECURITY: API key is read server-side from env. It is never sent to the browser.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class CoverLetterRequest(BaseModel):
    # Caller may pass either a job_id (look up from DB) or explicit title/company
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    resume_id: Optional[str] = None       # if provided, extract resume text from DB
    resume_summary: Optional[str] = None  # or pass text directly
    tone: Optional[str] = "professional"


class CoverLetterResponse(BaseModel):
    cover_letter: str
    word_count: int
    generated_by: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class InterviewPrepRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: Optional[str] = None
    focus_areas: Optional[str] = None   # e.g. "system design, python, ml"


class InterviewPrepResponse(BaseModel):
    questions: list
    tips: list
    generated_by: str


# ── Gemini helper ──────────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    """Call Gemini 1.5 Flash. Returns the text response or raises."""
    import httpx
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


# ── Cover-letter templates (fallback when no API key) ─────────────────────────

def _template_cover_letter(req: CoverLetterRequest) -> str:
    desc_snippet = ""
    if req.job_description:
        desc_snippet = f"\n\nThe role involves: {req.job_description[:300]}..."
    return (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my strong interest in the {req.job_title} position at {req.company_name}."
        f"{desc_snippet}\n\n"
        f"With a solid foundation in the relevant technical skills and a genuine passion for "
        f"building impactful products, I am confident in my ability to contribute meaningfully "
        f"to your team.\n\n"
        f"I would welcome the opportunity to discuss how my background aligns with the needs of "
        f"{req.company_name}.\n\n"
        f"Thank you for your time and consideration.\n\n"
        f"Sincerely,\n[Your Name]"
    )


def _template_interview_prep(req: InterviewPrepRequest) -> dict:
    return {
        "questions": [
            {"type": "behavioral", "question": f"Tell me about yourself and why you want to join {req.company_name}."},
            {"type": "behavioral", "question": "Describe a challenging project you worked on and what you learned."},
            {"type": "behavioral", "question": "How do you handle tight deadlines and competing priorities?"},
            {"type": "technical", "question": f"What relevant skills do you bring to the {req.job_title} role?"},
            {"type": "technical", "question": "Walk me through a system you designed or built end-to-end."},
            {"type": "situational", "question": "How would you approach onboarding in the first 30 days?"},
        ],
        "tips": [
            "Research the company's recent products, blog posts, and mission statement.",
            "Prepare 2–3 quantified achievements from past projects.",
            "Practice STAR (Situation/Task/Action/Result) method for behavioral answers.",
            "Prepare 2–3 thoughtful questions to ask the interviewer.",
            "Review the job description and map your skills to each requirement.",
        ],
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    req: CoverLetterRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Job as JobModel, Resume as ResumeModel

    # Resolve job from DB if job_id provided
    job_title = req.job_title or ""
    company_name = req.company_name or ""
    job_description = req.job_description or ""
    if req.job_id:
        job = await db.get(JobModel, req.job_id)
        if job:
            job_title = job.title or job_title
            company_name = job.company_name or company_name
            job_description = job.description or job_description

    if not job_title:
        raise HTTPException(status_code=400, detail="job_title or job_id is required")
    if not company_name:
        company_name = "the company"

    # Resolve resume summary from DB if resume_id provided
    resume_summary = req.resume_summary or ""
    if req.resume_id:
        resume = await db.get(ResumeModel, req.resume_id)
        if resume and resume.parsed_text:
            resume_summary = resume.parsed_text[:600]

    # Build a new request with resolved fields for the generation functions
    resolved = CoverLetterRequest(
        job_title=job_title,
        company_name=company_name,
        job_description=job_description[:600] if job_description else None,
        resume_summary=resume_summary or None,
        tone=req.tone,
    )

    if settings.gemini_api_key:
        prompt = (
            f"Write a {resolved.tone or 'professional'} cover letter for a {job_title} "
            f"position at {company_name}. "
        )
        if job_description:
            prompt += f"The job description says: {job_description[:600]}. "
        if resume_summary:
            prompt += f"The applicant's background: {resume_summary[:400]}. "
        prompt += (
            "Write 3 concise paragraphs. Do NOT include a placeholder name. "
            "Use [Your Name] at the end. Return only the letter text."
        )
        try:
            text = await _call_gemini(prompt)
            return CoverLetterResponse(
                cover_letter=text.strip(),
                word_count=len(text.split()),
                generated_by="gemini-1.5-flash",
                job_title=job_title,
                company_name=company_name,
            )
        except Exception as e:
            logger.warning(f"Gemini cover letter failed ({e}), using template")

    text = _template_cover_letter(resolved)
    return CoverLetterResponse(
        cover_letter=text,
        word_count=len(text.split()),
        generated_by="template",
        job_title=job_title,
        company_name=company_name,
    )


@router.post("/interview-prep", response_model=InterviewPrepResponse)
async def generate_interview_prep(
    req: InterviewPrepRequest,
    current_user: dict = Depends(get_current_user),
):
    if settings.gemini_api_key:
        prompt = (
            f"Generate 8 interview questions and 5 preparation tips for a {req.job_title} "
            f"role at {req.company_name}. "
        )
        if req.job_description:
            prompt += f"The job involves: {req.job_description[:500]}. "
        if req.focus_areas:
            prompt += f"Focus on: {req.focus_areas}. "
        prompt += (
            "Format your response as JSON with two keys: "
            '"questions" (array of {type, question}) and "tips" (array of strings). '
            "Return only the JSON."
        )
        try:
            import json
            raw = await _call_gemini(prompt)
            # Strip markdown fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:])
            if clean.endswith("```"):
                clean = "\n".join(clean.split("\n")[:-1])
            data = json.loads(clean)
            return InterviewPrepResponse(
                questions=data.get("questions", []),
                tips=data.get("tips", []),
                generated_by="gemini-1.5-flash",
            )
        except Exception as e:
            logger.warning(f"Gemini interview prep failed ({e}), using template")

    tmpl = _template_interview_prep(req)
    return InterviewPrepResponse(**tmpl, generated_by="template")
