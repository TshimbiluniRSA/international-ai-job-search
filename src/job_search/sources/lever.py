from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from ..models import Job
from .http import get_json


def _plain(value: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def _created_at(value: Any) -> str | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def normalize_lever(payload: list[dict[str, Any]], company: str) -> list[Job]:
    jobs: list[Job] = []
    for item in payload:
        categories = item.get("categories") or {}
        description_parts = [item.get("descriptionPlain", "")]
        description_parts.extend(section.get("content", "") for section in item.get("lists", []))
        jobs.append(
            Job(
                source="lever",
                source_id=item.get("id", ""),
                company=company,
                title=item.get("text", ""),
                location=categories.get("location", ""),
                url=item.get("hostedUrl", ""),
                description=_plain(" ".join(description_parts)),
                posted_at=_created_at(item.get("createdAt")),
            )
        )
    return jobs


def fetch_lever(company: str, slug: str) -> list[Job]:
    company_slug = quote(slug, safe="")
    payload = get_json(f"https://api.lever.co/v0/postings/{company_slug}?mode=json")
    return normalize_lever(payload, company)
