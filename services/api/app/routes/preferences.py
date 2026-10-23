"""
User job-search preferences — target roles, skills, location, salary, work mode.
GET  /api/preferences/   → return current profile
PUT  /api/preferences/   → upsert profile
"""

import json
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.models import UserProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/preferences", tags=["preferences"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class PreferencesOut(BaseModel):
    target_roles: List[str] = []
    preferred_locations: List[str] = []
    preferred_job_types: List[str] = []   # frontend uses this field
    skills: List[str] = []
    graduation_year: Optional[int] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None
    salary_min_lpa: Optional[int] = None
    min_salary: Optional[str] = None      # frontend uses this string field
    open_to_remote: bool = True

    class Config:
        orm_mode = True


class PreferencesIn(BaseModel):
    target_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    graduation_year: Optional[int] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None
    salary_min_lpa: Optional[int] = None
    min_salary: Optional[str] = None      # alternative to salary_min_lpa for frontend compat
    open_to_remote: Optional[bool] = None

    @validator("experience_level")
    def validate_experience(cls, v):
        if v and v not in ("fresher", "entry", "mid", "senior", "any"):
            raise ValueError("experience_level must be fresher/entry/mid/senior/any")
        return v

    @validator("work_mode")
    def validate_work_mode(cls, v):
        if v and v not in ("onsite", "hybrid", "remote", "any"):
            raise ValueError("work_mode must be onsite/hybrid/remote/any")
        return v


def _to_json(lst: Optional[List[str]]) -> Optional[str]:
    return json.dumps(lst) if lst is not None else None


def _from_json(text: Optional[str]) -> List[str]:
    if not text:
        return []
    try:
        val = json.loads(text)
        return val if isinstance(val, list) else []
    except Exception:
        return []


def _profile_to_out(profile: UserProfile) -> dict:
    salary_lpa = profile.salary_min_lpa
    return {
        "target_roles": _from_json(profile.target_roles),
        "preferred_locations": _from_json(profile.preferred_locations),
        "preferred_job_types": _from_json(getattr(profile, "preferred_job_types", None)),
        "skills": _from_json(profile.skills),
        "graduation_year": profile.graduation_year,
        "experience_level": profile.experience_level,
        "work_mode": profile.work_mode,
        "salary_min_lpa": salary_lpa,
        "min_salary": str(salary_lpa) if salary_lpa is not None else None,
        "open_to_remote": profile.open_to_remote,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=PreferencesOut)
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalars().first()
    if not profile:
        # Return defaults with the configured initial preferences
        return PreferencesOut(
            target_roles=["AI Engineer", "ML Engineer", "Data Scientist",
                          "Applied AI Engineer", "Python Developer", "Software Engineer"],
            preferred_locations=["India", "Bangalore", "Hyderabad", "Mumbai", "Pune", "Chennai"],
            preferred_job_types=["Full-time", "Internship"],
            graduation_year=2027,
            experience_level="fresher",
            work_mode="hybrid",
            salary_min_lpa=10,
            min_salary="10",
            open_to_remote=False,
        )
    return PreferencesOut(**_profile_to_out(profile))


@router.put("/", response_model=PreferencesOut)
async def update_preferences(
    body: PreferencesIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalars().first()

    if not profile:
        profile = UserProfile(id=str(uuid.uuid4()), user_id=user_id)
        db.add(profile)

    if body.target_roles is not None:
        profile.target_roles = _to_json(body.target_roles)
    if body.preferred_locations is not None:
        profile.preferred_locations = _to_json(body.preferred_locations)
    if body.skills is not None:
        profile.skills = _to_json(body.skills)
    if body.graduation_year is not None:
        profile.graduation_year = body.graduation_year
    if body.experience_level is not None:
        profile.experience_level = body.experience_level
    if body.work_mode is not None:
        profile.work_mode = body.work_mode
    if body.salary_min_lpa is not None:
        profile.salary_min_lpa = body.salary_min_lpa
    elif body.min_salary is not None:
        # Frontend sends min_salary as a string; try to parse an integer out of it
        try:
            profile.salary_min_lpa = int("".join(filter(str.isdigit, body.min_salary)) or "0") or None
        except Exception:
            pass
    if body.preferred_job_types is not None:
        profile.preferred_job_types = _to_json(body.preferred_job_types)
    if body.open_to_remote is not None:
        profile.open_to_remote = body.open_to_remote

    await db.commit()
    await db.refresh(profile)
    return PreferencesOut(**_profile_to_out(profile))
