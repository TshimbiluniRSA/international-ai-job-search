from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import load_json, save_json
from .models import RankedJob


APPLICATION_STATUSES = {
    "discovered",
    "qualified",
    "materials_ready",
    "applied",
    "recruiter_contact",
    "interview",
    "technical_assessment",
    "offer",
    "rejected",
    "archived",
}


def load_tracker(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = load_json(path)
    if not isinstance(value, list):
        raise ValueError("Application tracker must contain a JSON list")
    return value


def track_job(
    ranked: RankedJob,
    tracker_path: Path,
    status: str,
    notes: str | None = None,
) -> dict[str, Any]:
    if status not in APPLICATION_STATUSES:
        raise ValueError(f"Unknown application status: {status}")

    records = load_tracker(tracker_path)
    now = datetime.now(UTC).isoformat()
    existing = next((record for record in records if record["url"] == ranked.job.url), None)
    if existing:
        existing["status"] = status
        existing["updated_at"] = now
        existing["score"] = ranked.score
        existing["eligibility"] = ranked.eligibility.status
        if notes:
            existing["notes"] = notes
        record = existing
    else:
        record = {
            "company": ranked.job.company,
            "title": ranked.job.title,
            "url": ranked.job.url,
            "source": ranked.job.source,
            "location": ranked.job.location,
            "score": ranked.score,
            "eligibility": ranked.eligibility.status,
            "status": status,
            "discovered_at": now,
            "updated_at": now,
            "applied_at": now if status == "applied" else None,
            "notes": notes or "",
        }
        records.append(record)

    if status == "applied" and not record.get("applied_at"):
        record["applied_at"] = now
    save_json(tracker_path, records)
    return record
