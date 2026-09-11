from __future__ import annotations

from pathlib import Path

from .application_policy import evaluate_application_policy
from .models import RankedJob
from .scoring import APPLICATION_THRESHOLD


def create_shortlist(items: list[RankedJob], destination: Path, limit: int = 20) -> Path:
    selected = [
        item
        for item in items
        if item.score >= APPLICATION_THRESHOLD and item.recommendation == "apply now"
    ][:limit]
    lines = [
        "# International job shortlist",
        "",
        (
            f"Only roles scoring at least {APPLICATION_THRESHOLD}/100 are included. "
            "Remote roles with no explicit geographic restriction are treated as "
            "provisionally eligible; explicit location and work-authorization restrictions "
            "still exclude a role."
        ),
        (
            "If a posting explicitly prohibits AI-assisted application content, it requires "
            "manual materials. If no AI restriction is found, the role is application-ready. "
            "Every submission remains subject to human review."
        ),
        "",
    ]
    if not selected:
        lines.append(
            f"No eligible jobs scoring at least {APPLICATION_THRESHOLD}/100 were found "
            "in this run."
        )
    for index, item in enumerate(selected, start=1):
        job = item.job
        policy = evaluate_application_policy(job)
        lines.extend(
            [
                f"## {index}. {job.company} — {job.title}",
                "",
                f"- Score: **{item.score}/100**",
                f"- Eligibility: **{item.eligibility.status}**",
                f"- Recommendation: **{item.recommendation}**",
                f"- Application policy: **{policy.status}**",
                f"- Next action: {policy.next_action}",
                f"- Location: {job.location or 'Not stated'}",
                f"- Source: [{job.source}]({job.url})",
                f"- Strongest match: {item.strengths[0] if item.strengths else 'No strong match extracted'}",
                f"- Main gap: {item.gaps[0] if item.gaps else 'No material gap detected'}",
                f"- Policy evidence: {policy.evidence}",
                "",
            ]
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
