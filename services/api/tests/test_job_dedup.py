"""Tests for job deduplication service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.job_dedup import upsert_jobs


def _make_job(title="SWE Intern", company="Stripe", location="SF, CA", source="greenhouse", ext_id="123"):
    from app.services.job_sources import _dedupe_sig
    return {
        "source": source,
        "external_id": ext_id,
        "title": title,
        "description": "A job description.",
        "location": location,
        "company_name": company,
        "apply_url": "https://example.com/apply",
        "salary_range": None,
        "job_type": "Internship",
        "posted_at": "2025-01-15T10:00:00+00:00",
        "dedupe_signature": _dedupe_sig(title, company, location),
    }


@pytest.mark.asyncio
async def test_upsert_inserts_new_jobs():
    """New jobs should be inserted."""
    db = AsyncMock(spec=AsyncSession)

    # No existing sigs or ids
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    jobs = [_make_job()]
    inserted, skipped = await upsert_jobs(db, jobs)

    assert inserted == 1
    assert skipped == 0
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_skips_duplicate_external_id():
    """Jobs with same (source, external_id) should be skipped."""
    db = AsyncMock(spec=AsyncSession)

    call_count = 0

    async def fake_execute(stmt):
        nonlocal call_count
        mock_result = MagicMock()
        if call_count == 0:
            # First call: existing signatures query
            mock_result.scalars.return_value.all.return_value = []
            call_count += 1
        else:
            # Second call: existing (source, ext_id) pairs
            mock_result.all.return_value = [("greenhouse", "123")]
            call_count += 1
        return mock_result

    db.execute = fake_execute

    jobs = [_make_job(ext_id="123")]
    inserted, skipped = await upsert_jobs(db, jobs)

    assert inserted == 0
    assert skipped == 1


@pytest.mark.asyncio
async def test_upsert_handles_empty_list():
    db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    inserted, skipped = await upsert_jobs(db, [])
    assert inserted == 0
    assert skipped == 0
    db.commit.assert_not_called()
