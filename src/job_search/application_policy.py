from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Job

AI_RESTRICTED = re.compile(
    r"(?:do not|must not|may not|cannot|can't|prohibited|forbidden|not permitted)"
    r".{0,80}(?:artificial intelligence|generative ai|ai-generated|\bai\b)"
    r"|(?:artificial intelligence|generative ai|ai-generated|\bai\b)"
    r".{0,80}(?:prohibited|forbidden|not permitted|will disqualify)",
    re.IGNORECASE | re.DOTALL,
)

AI_ALLOWED = re.compile(
    r"(?:artificial intelligence|generative ai|ai assistance|ai tools)"
    r".{0,80}(?:allowed|permitted|welcome|may be used|can be used)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class ApplicationPolicy:
    status: str
    evidence: str
    next_action: str


def evaluate_application_policy(job: Job) -> ApplicationPolicy:
    text = f"{job.title}\n{job.description}"
    if AI_RESTRICTED.search(text):
        return ApplicationPolicy(
            status="manual_materials_required",
            evidence="The posting explicitly restricts AI-assisted application content.",
            next_action="Apply manually using only the candidate's own words.",
        )
    if AI_ALLOWED.search(text):
        return ApplicationPolicy(
            status="ai_assistance_allowed",
            evidence="The posting explicitly allows AI assistance.",
            next_action="Prepare truthful application materials for review.",
        )
    return ApplicationPolicy(
        status="no_ai_restriction_found",
        evidence="No restriction on AI-assisted application materials was found in the posting.",
        next_action="Prepare truthful application materials for review.",
    )
