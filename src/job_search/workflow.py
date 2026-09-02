from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import save_json
from .models import RankedJob

ACTIONABLE_RECOMMENDATIONS = {
    "apply now",
    "good match",
    "manual review",
    "verify hiring location",
}


def create_application_queue(
    items: list[RankedJob],
    destination: Path,
    limit: int = 10,
) -> Path:
    selected = [
        item
        for item in items
        if item.recommendation in ACTIONABLE_RECOMMENDATIONS
    ][:limit]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "submission_mode": "human_approved",
        "preferred_cv_format": "pdf",
        "items": [],
    }
    for item in selected:
        payload["items"].append(
            {
                "company": item.job.company,
                "title": item.job.title,
                "url": item.job.url,
                "location": item.job.location,
                "score": item.score,
                "eligibility": item.eligibility.status,
                "recommendation": item.recommendation,
                "status": "qualified",
                "required_actions": [
                    "verify_hiring_location",
                    "inspect_application_ai_policy",
                    "prepare_truthful_pdf_cv",
                    "human_review",
                    "approve_final_submission",
                    "verify_submission_confirmation",
                    "monitor_inbox_feedback",
                ],
            }
        )
    return save_json(destination, payload)
