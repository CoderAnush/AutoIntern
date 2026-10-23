"""
Real job source adapters — India-first edition.

Supported adapter types:
  - greenhouse  : Greenhouse Embedded Job Board API (public, no auth)
  - lever       : Lever Postings API (public, no auth)
  - remoteok    : RemoteOK public JSON API (https://remoteok.com/api)

Company registry is driven by india_companies.INDIA_COMPANY_REGISTRY.
RemoteOK is included for additional volume but marked non-Indian.

NO credentials, CAPTCHAs, or scraping are used — only documented public APIs.
"""

import asyncio
import hashlib
import html as html_lib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.services.india_companies import get_active_adapters, get_indian_origin_names

logger = logging.getLogger(__name__)

# Built once at import; used for India-priority ranking at ingest time.
_INDIAN_NAMES: set[str] = get_indian_origin_names()


def _is_indian_company(name: str) -> bool:
    return name.strip().lower() in _INDIAN_NAMES


# ── Normalisation helpers ─────────────────────────────────────────────────────

def _dedupe_sig(title: str, company: str, location: str) -> str:
    raw = f"{title.strip().lower()}|{company.strip().lower()}|{location.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_strip(v: Any, max_len: int = 512) -> Optional[str]:
    if not v:
        return None
    return str(v).strip()[:max_len]


def _strip_html(text: str) -> str:
    """Strip HTML tags and decode entities to plain text (stdlib only)."""
    if not text:
        return ""
    # Decode HTML entities first (e.g. &lt; → <, &amp; → &)
    text = html_lib.unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# ── Greenhouse adapter ────────────────────────────────────────────────────────

async def _fetch_greenhouse(client: httpx.AsyncClient, company: dict) -> list[dict]:
    token = company["board_token"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    jobs = []
    try:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Greenhouse {token}: HTTP {resp.status_code}")
            return jobs
        data = resp.json()
        raw_jobs = data.get("jobs", [])
        logger.info(f"Greenhouse {company['name']}: {len(raw_jobs)} listings")
        for j in raw_jobs:
            location = _safe_strip(j.get("location", {}).get("name", "")) or "India / Remote"
            title = _safe_strip(j.get("title", "")) or "Unknown"
            apply_url = _safe_strip(j.get("absolute_url", ""))
            # Strip HTML from the `content` field before storing
            raw_desc = j.get("content", "") or ""
            description = _strip_html(raw_desc)[:8000]
            updated = j.get("updated_at", "")
            try:
                posted_at = datetime.fromisoformat(updated.replace("Z", "+00:00")).isoformat()
            except Exception:
                posted_at = _now_utc()

            jobs.append({
                "source": "greenhouse",
                "external_id": str(j.get("id", "")),
                "title": title,
                "description": description,
                "location": location,
                "company_name": company["name"],
                "apply_url": apply_url,
                "salary_range": None,
                "job_type": _infer_job_type(title, description),
                "posted_at": posted_at,
                "dedupe_signature": _dedupe_sig(title, company["name"], location),
                "is_india_job": _is_indian_company(company["name"]),
            })
    except Exception as e:
        logger.error(f"Greenhouse {token}: {e}")
    return jobs


# ── Lever adapter ─────────────────────────────────────────────────────────────

async def _fetch_lever(client: httpx.AsyncClient, company: dict) -> list[dict]:
    token = company["board_token"]
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    jobs = []
    try:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Lever {token}: HTTP {resp.status_code}")
            return jobs
        raw_jobs = resp.json()
        if not isinstance(raw_jobs, list):
            raw_jobs = raw_jobs.get("postings", [])
        logger.info(f"Lever {company['name']}: {len(raw_jobs)} listings")
        for j in raw_jobs:
            location = _safe_strip(j.get("categories", {}).get("location", "")) or "India / Remote"
            title = _safe_strip(j.get("text", "")) or "Unknown"
            apply_url = _safe_strip(j.get("hostedUrl", ""))
            # Lever descriptionPlain is generally plain text but lists may have HTML
            desc_parts = j.get("descriptionPlain", "") or j.get("description", "") or ""
            lists = j.get("lists", [])
            for lst in lists:
                item_text = lst.get("text", "") + "\n" + lst.get("content", "")
                desc_parts += "\n" + _strip_html(item_text)
            description = _strip_html(desc_parts)[:8000]
            created_at_ms = j.get("createdAt", 0)
            try:
                posted_at = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc).isoformat()
            except Exception:
                posted_at = _now_utc()

            jobs.append({
                "source": "lever",
                "external_id": (_safe_strip(j.get("id", "")) or "")[:255],
                "title": title,
                "description": description,
                "location": location,
                "company_name": company["name"],
                "apply_url": apply_url,
                "salary_range": None,
                "job_type": _infer_job_type(title, description),
                "posted_at": posted_at,
                "dedupe_signature": _dedupe_sig(title, company["name"], location),
                "is_india_job": _is_indian_company(company["name"]),
            })
    except Exception as e:
        logger.error(f"Lever {token}: {e}")
    return jobs


# ── RemoteOK adapter ──────────────────────────────────────────────────────────

async def _fetch_remoteok(client: httpx.AsyncClient, company: dict) -> list[dict]:
    url = company["url"]
    jobs = []
    try:
        resp = await client.get(url, timeout=20, headers={"User-Agent": "AutoIntern/1.0 job aggregator"})
        if resp.status_code != 200:
            logger.warning(f"RemoteOK: HTTP {resp.status_code}")
            return jobs
        raw = resp.json()
        raw_jobs = [j for j in raw if isinstance(j, dict) and j.get("id")]
        logger.info(f"RemoteOK: {len(raw_jobs)} listings")
        for j in raw_jobs[:50]:
            title = _safe_strip(j.get("position", "")) or "Unknown"
            company_name = _safe_strip(j.get("company", "RemoteOK")) or "RemoteOK"
            location = "Remote"
            apply_url = _safe_strip(j.get("url", ""))
            description = _strip_html(_safe_strip(j.get("description", ""), 8000) or "")
            tags = j.get("tags", [])
            if tags:
                description = "Tags: " + ", ".join(tags) + "\n\n" + description
            epoch = j.get("date", 0)
            try:
                posted_at = datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
            except Exception:
                posted_at = _now_utc()

            jobs.append({
                "source": "remoteok",
                "external_id": str(j.get("id", ""))[:255],
                "title": title,
                "description": description,
                "location": location,
                "company_name": company_name,
                "apply_url": apply_url,
                "salary_range": _format_salary(j.get("salary_min"), j.get("salary_max")),
                "job_type": "Remote",
                "posted_at": posted_at,
                "dedupe_signature": _dedupe_sig(title, company_name, location),
                "is_india_job": False,
            })
    except Exception as e:
        logger.error(f"RemoteOK: {e}")
    return jobs


# ── Helpers ───────────────────────────────────────────────────────────────────

def _infer_job_type(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    if any(k in text for k in ("intern", "internship", "co-op", "coop", "trainee", "fresher")):
        return "Internship"
    if any(k in text for k in ("contract", "freelance", "temporary", "contractual")):
        return "Contract"
    if any(k in text for k in ("part-time", "part time")):
        return "Part-time"
    return "Full-time"


def _format_salary(min_sal, max_sal) -> Optional[str]:
    try:
        if min_sal and max_sal:
            return f"${int(min_sal):,}–${int(max_sal):,}/yr"
        if min_sal:
            return f"${int(min_sal):,}+/yr"
    except Exception:
        pass
    return None


# ── Build the company registry from india_companies.py ───────────────────────

_INDIA_ADAPTERS = get_active_adapters()

# Full registry: all active Indian company adapters + RemoteOK for global volume
COMPANY_REGISTRY: list[dict] = _INDIA_ADAPTERS + [
    {"name": "RemoteOK", "adapter": "remoteok", "url": "https://remoteok.com/api",
     "is_indian_origin": False},
]

# ── Public entry point ────────────────────────────────────────────────────────

_ADAPTERS = {
    "greenhouse": _fetch_greenhouse,
    "lever":      _fetch_lever,
    "remoteok":   _fetch_remoteok,
}


async def collect_all_jobs() -> list[dict]:
    """Fetch jobs from all configured sources concurrently."""
    all_jobs: list[dict] = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for company in COMPANY_REGISTRY:
            adapter_fn = _ADAPTERS.get(company["adapter"])
            if adapter_fn:
                tasks.append(adapter_fn(client, company))
            else:
                logger.warning(f"Unknown adapter '{company['adapter']}' for {company['name']}")

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Source error: {result}")
            elif isinstance(result, list):
                all_jobs.extend(result)

    india_count = sum(1 for j in all_jobs if j.get("is_india_job"))
    logger.info(
        f"Total jobs collected: {len(all_jobs)} "
        f"(Indian companies: {india_count}, other: {len(all_jobs) - india_count})"
    )
    return all_jobs
