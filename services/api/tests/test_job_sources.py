"""Tests for real job source adapters.

These tests use mocked HTTP responses so they run without network access.
Run with: pytest tests/test_job_sources.py -v
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.job_sources import (
    _fetch_greenhouse,
    _fetch_lever,
    _fetch_remoteok,
    _infer_job_type,
    _format_salary,
    collect_all_jobs,
    COMPANY_REGISTRY,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

GREENHOUSE_RESPONSE = {
    "jobs": [
        {
            "id": 12345,
            "title": "Software Engineer Intern",
            "location": {"name": "San Francisco, CA"},
            "absolute_url": "https://boards.greenhouse.io/stripe/jobs/12345",
            "content": "We are looking for a software engineering intern...",
            "updated_at": "2025-01-15T10:00:00Z",
        }
    ]
}

LEVER_RESPONSE = [
    {
        "id": "abc-123",
        "text": "Backend Engineer",
        "hostedUrl": "https://jobs.lever.co/airtable/abc-123",
        "categories": {"location": "Remote"},
        "descriptionPlain": "Build scalable backend services...",
        "lists": [],
        "createdAt": 1705315200000,
    }
]

REMOTEOK_RESPONSE = [
    {"legal": "terms"},  # First element is always legal notice
    {
        "id": "rk-001",
        "position": "Senior React Developer",
        "company": "Cool Startup",
        "url": "https://remoteok.com/l/rk-001",
        "description": "React TypeScript GraphQL",
        "tags": ["react", "typescript"],
        "date": "1705315200",
        "salary_min": 120000,
        "salary_max": 160000,
    },
]


def _make_response(data, status_code=200):
    mock = AsyncMock(spec=httpx.AsyncClient)
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = data
    return response


# ── Greenhouse ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_greenhouse_returns_jobs():
    company = {"name": "Stripe", "adapter": "greenhouse", "board_token": "stripe"}
    client = AsyncMock()
    client.get.return_value = _make_response(GREENHOUSE_RESPONSE)

    jobs = await _fetch_greenhouse(client, company)

    assert len(jobs) == 1
    j = jobs[0]
    assert j["title"] == "Software Engineer Intern"
    assert j["company_name"] == "Stripe"
    assert j["source"] == "greenhouse"
    assert j["external_id"] == "12345"
    assert j["location"] == "San Francisco, CA"
    assert j["apply_url"].startswith("https://")
    assert j["dedupe_signature"]  # non-empty MD5


@pytest.mark.asyncio
async def test_greenhouse_404_returns_empty():
    company = {"name": "Stripe", "adapter": "greenhouse", "board_token": "nonexistent"}
    client = AsyncMock()
    client.get.return_value = _make_response({}, status_code=404)

    jobs = await _fetch_greenhouse(client, company)
    assert jobs == []


# ── Lever ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lever_returns_jobs():
    company = {"name": "Airtable", "adapter": "lever", "board_token": "airtable"}
    client = AsyncMock()
    client.get.return_value = _make_response(LEVER_RESPONSE)

    jobs = await _fetch_lever(client, company)

    assert len(jobs) == 1
    j = jobs[0]
    assert j["title"] == "Backend Engineer"
    assert j["company_name"] == "Airtable"
    assert j["source"] == "lever"
    assert j["location"] == "Remote"


@pytest.mark.asyncio
async def test_lever_404_returns_empty():
    company = {"name": "Airtable", "adapter": "lever", "board_token": "nonexistent"}
    client = AsyncMock()
    client.get.return_value = _make_response([], status_code=404)

    jobs = await _fetch_lever(client, company)
    assert jobs == []


# ── RemoteOK ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remoteok_skips_legal_notice():
    company = {"name": "RemoteOK", "adapter": "remoteok", "url": "https://remoteok.com/api"}
    client = AsyncMock()
    client.get.return_value = _make_response(REMOTEOK_RESPONSE)

    jobs = await _fetch_remoteok(client, company)

    assert len(jobs) == 1  # legal notice object skipped
    j = jobs[0]
    assert j["title"] == "Senior React Developer"
    assert j["company_name"] == "Cool Startup"
    assert j["salary_range"] == "$120,000–$160,000/yr"
    assert j["job_type"] == "Remote"


# ── Helpers ───────────────────────────────────────────────────────────────────

def test_infer_job_type_internship():
    assert _infer_job_type("Software Engineer Intern", "") == "Internship"
    assert _infer_job_type("SWE Internship Summer 2025", "") == "Internship"


def test_infer_job_type_contract():
    assert _infer_job_type("Senior Engineer", "contract role for 6 months") == "Contract"


def test_infer_job_type_fulltime_default():
    assert _infer_job_type("Backend Engineer", "full stack development") == "Full-time"


def test_format_salary_range():
    assert _format_salary(120000, 160000) == "$120,000–$160,000/yr"


def test_format_salary_min_only():
    assert _format_salary(100000, None) == "$100,000+/yr"


def test_format_salary_none():
    assert _format_salary(None, None) is None


# ── Registry ──────────────────────────────────────────────────────────────────

def test_registry_has_minimum_companies():
    assert len(COMPANY_REGISTRY) >= 20


def test_registry_all_have_required_fields():
    for company in COMPANY_REGISTRY:
        assert "name" in company
        assert "adapter" in company
        assert company["adapter"] in ("greenhouse", "lever", "remoteok", "workday")


# ── Deduplication ─────────────────────────────────────────────────────────────

def test_dedupe_signature_consistent():
    from app.services.job_sources import _dedupe_sig
    s1 = _dedupe_sig("Software Engineer", "Stripe", "San Francisco, CA")
    s2 = _dedupe_sig("Software Engineer", "Stripe", "San Francisco, CA")
    assert s1 == s2
    assert len(s1) == 32  # MD5 hex


def test_dedupe_signature_different_companies():
    from app.services.job_sources import _dedupe_sig
    s1 = _dedupe_sig("Software Engineer", "Stripe", "San Francisco, CA")
    s2 = _dedupe_sig("Software Engineer", "Airbnb", "San Francisco, CA")
    assert s1 != s2
