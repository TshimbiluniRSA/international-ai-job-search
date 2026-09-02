from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import load_json, save_json
from .models import RankedJob

APPLICATION_STATUSES = {
    "discovered",
    "qualified",
    "eligibility_verified",
    "manual_materials_required",
    "materials_draft",
    "materials_ready",
    "approved_to_submit",
    "applied",
    "confirmation_received",
    "recruiter_contact",
    "interview",
    "technical_assessment",
    "offer",
    "rejected",
    "withdrawn",
    "archived",
}


def load_tracker(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = load_json(path)
    if not isinstance(value, list):
        raise TypeError("Application tracker must contain a JSON list")
    return value


def track_job(
    ranked: RankedJob,
    tracker_path: Path,
    status: str,
    notes: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in APPLICATION_STATUSES:
        raise ValueError(f"Unknown application status: {status}")

    records = load_tracker(tracker_path)
    now = datetime.now(UTC).isoformat()
    existing = next((record for record in records if record["url"] == ranked.job.url), None)
    if existing:
        previous_status = existing["status"]
        existing["status"] = status
        existing["updated_at"] = now
        existing["score"] = ranked.score
        existing["eligibility"] = ranked.eligibility.status
        if notes:
            existing["notes"] = notes
        existing.setdefault("events", []).append(
            {"at": now, "type": "status_changed", "from": previous_status, "to": status}
        )
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
            "confirmation_received_at": None,
            "cv_path": None,
            "application_policy": "unchecked",
            "confirmation_email_id": None,
            "last_email_at": None,
            "next_action": None,
            "next_action_due": None,
            "notes": notes or "",
            "events": [{"at": now, "type": "created", "status": status}],
        }
        records.append(record)

    if status == "applied" and not record.get("applied_at"):
        record["applied_at"] = now
    if status == "confirmation_received" and not record.get("confirmation_received_at"):
        record["confirmation_received_at"] = now
    if metadata:
        for key, value in metadata.items():
            if value is not None:
                record[key] = value
    save_json(tracker_path, records)
    return record


def update_application(
    tracker_path: Path,
    url: str,
    status: str,
    notes: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in APPLICATION_STATUSES:
        raise ValueError(f"Unknown application status: {status}")
    records = load_tracker(tracker_path)
    record = next((item for item in records if item["url"] == url), None)
    if record is None:
        raise ValueError(f"Application is not tracked: {url}")

    now = datetime.now(UTC).isoformat()
    previous_status = record["status"]
    record["status"] = status
    record["updated_at"] = now
    if notes:
        record["notes"] = notes
    record.setdefault("events", []).append(
        {"at": now, "type": "status_changed", "from": previous_status, "to": status}
    )
    if status == "applied" and not record.get("applied_at"):
        record["applied_at"] = now
    if status == "confirmation_received" and not record.get("confirmation_received_at"):
        record["confirmation_received_at"] = now
    if metadata:
        for key, value in metadata.items():
            if value is not None:
                record[key] = value
    save_json(tracker_path, records)
    return record
