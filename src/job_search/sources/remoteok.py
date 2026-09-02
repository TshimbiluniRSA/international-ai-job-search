from __future__ import annotations

import html
import re
from typing import Any

from ..models import Job
from .http import get_json


API_URL = "https://remoteok.com/api"


def _plain(value: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def normalize_remoteok(payload: list[dict[str, Any]], keywords: list[str]) -> list[Job]:
    wanted = [keyword.casefold() for keyword in keywords]
    jobs: list[Job] = []
    for item in payload:
        if "position" not in item:  # The first API item contains feed metadata.
            continue
        title = item.get("position", "")
        description = _plain(item.get("description"))
        tags = " ".join(item.get("tags") or [])
        searchable = " ".join((title, description, tags)).casefold()
        if wanted and not any(keyword in searchable for keyword in wanted):
            continue
        jobs.append(
            Job(
                source="remoteok",
                source_id=str(item.get("id", "")),
                company=item.get("company", ""),
                title=title,
                location=item.get("location") or "Remote",
                url=item.get("url", ""),
                description=description,
                posted_at=item.get("date"),
            )
        )
    return jobs


def fetch_remoteok(keywords: list[str]) -> list[Job]:
    payload = get_json(API_URL)
    return normalize_remoteok(payload, keywords)
