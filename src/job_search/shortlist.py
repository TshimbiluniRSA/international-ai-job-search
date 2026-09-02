from __future__ import annotations

from pathlib import Path

from .models import RankedJob

INCLUDED_RECOMMENDATIONS = {
    "apply now",
    "good match",
    "manual review",
    "verify hiring location",
}


def create_shortlist(items: list[RankedJob], destination: Path, limit: int = 20) -> Path:
    selected = [
        item for item in items if item.recommendation in INCLUDED_RECOMMENDATIONS
    ][:limit]
    lines = [
        "# International job shortlist",
        "",
        "Roles are ranked against verified candidate evidence. Final eligibility and every application remain subject to human review.",
        "",
    ]
    if not selected:
        lines.append("No qualified jobs were found in this run.")
    for index, item in enumerate(selected, start=1):
        job = item.job
        lines.extend(
            [
                f"## {index}. {job.company} — {job.title}",
                "",
                f"- Score: **{item.score}/100**",
                f"- Eligibility: **{item.eligibility.status}**",
                f"- Recommendation: **{item.recommendation}**",
                f"- Location: {job.location or 'Not stated'}",
                f"- Source: [{job.source}]({job.url})",
                f"- Strongest match: {item.strengths[0] if item.strengths else 'No strong match extracted'}",
                f"- Main gap: {item.gaps[0] if item.gaps else 'No material gap detected'}",
                "",
            ]
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
