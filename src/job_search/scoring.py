from __future__ import annotations

import re
from typing import Any

from .eligibility import evaluate_eligibility
from .models import Job, RankedJob


ROLE_TERMS = {
    "python": ["python developer", "python engineer", "python"],
    "backend": ["backend engineer", "back-end engineer", "backend developer"],
    "full-stack": ["full stack", "full-stack"],
    "software": ["software engineer", "software developer"],
    "ai-automation": ["ai engineer", "automation engineer", "llm engineer", "applied ai"],
}

SENIOR_ONLY = re.compile(r"\b(?:staff|principal|lead|director|manager|architect)\b", re.I)


def _contains(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.I) is not None


def rank_job(job: Job, profile: dict[str, Any]) -> RankedJob:
    eligibility = evaluate_eligibility(job)
    text = " ".join((job.title, job.description)).lower()
    strengths: list[str] = []
    gaps: list[str] = []

    matched_skills = [skill for skill in profile["core_skills"] if _contains(text, skill)]
    skill_score = min(45, len(matched_skills) * 5)
    if matched_skills:
        strengths.append("Matching skills: " + ", ".join(matched_skills[:9]))
        evidence_map = profile.get("skill_evidence", {})
        grounded = [
            f"{skill}: {evidence_map[skill][0]}"
            for skill in matched_skills
            if skill in evidence_map and evidence_map[skill]
        ]
        if grounded:
            strengths.append("Verified evidence: " + "; ".join(grounded[:3]))
    else:
        gaps.append("No explicit core-skill match found")

    matched_role_groups = [
        group for group, terms in ROLE_TERMS.items() if any(term in text for term in terms)
    ]
    role_score = min(25, len(matched_role_groups) * 10)
    if matched_role_groups:
        strengths.append("Target role alignment: " + ", ".join(matched_role_groups))
    else:
        gaps.append("Title is outside the primary target-role set")

    evidence_score = 15 if any(term in text for term in ("api", "automation", "cloud", "ai", "llm")) else 5
    if evidence_score == 15:
        strengths.append("The role maps to documented production or portfolio evidence")

    level_score = 10
    if SENIOR_ONLY.search(job.title):
        level_score = 0
        gaps.append("Seniority appears above the current primary target")

    eligibility_score = {"eligible": 5, "verify": 0, "ineligible": 0}[eligibility.status]
    score = min(100, skill_score + role_score + evidence_score + level_score + eligibility_score)

    if eligibility.status == "ineligible":
        recommendation = "reject"
        score = 0
    elif eligibility.status == "verify":
        recommendation = "verify hiring location" if score >= 50 else "archive"
    elif score >= 80:
        recommendation = "apply now"
    elif score >= 65:
        recommendation = "good match"
    elif score >= 50:
        recommendation = "manual review"
    else:
        recommendation = "archive"

    return RankedJob(job, eligibility, score, strengths, gaps, recommendation)
