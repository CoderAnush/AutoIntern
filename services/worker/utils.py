import hashlib
from typing import Dict, Any


def make_dedupe_signature(payload: Dict[str, Any]) -> str:
    """Create a stable signature for deduplication from job fields.

    Uses title, external_id, company, location, and normalized description snippet.
    """
    parts = [
        str(payload.get("external_id", "")).strip(),
        str(payload.get("title", "")).strip().lower(),
        str(payload.get("company", "")).strip().lower(),
        str(payload.get("location", "")).strip().lower(),
    ]
    concat = "|".join(parts)
    return hashlib.sha256(concat.encode("utf-8")).hexdigest()
