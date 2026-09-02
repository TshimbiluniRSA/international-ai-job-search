from __future__ import annotations

import html
import re
from urllib.parse import quote

from ..models import Job
from .http import get_json


def _plain(value: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def fetch_greenhouse(company: str, board_token: str) -> list[Job]:
    token = quote(board_token, safe="")
    payload = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    jobs: list[Job] = []
    for item in payload.get("jobs", []):
        jobs.append(
            Job(
                source="greenhouse",
                source_id=str(item["id"]),
                company=company,
                title=item.get("title", ""),
                location=(item.get("location") or {}).get("name", ""),
                url=item.get("absolute_url", ""),
                description=_plain(item.get("content")),
                posted_at=item.get("updated_at"),
            )
        )
    return jobs
