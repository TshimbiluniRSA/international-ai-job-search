from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import RankedJob


def create_dossier(ranked: RankedJob, profile: dict[str, Any], destination: Path) -> Path:
    job = ranked.job
    evidence = _profile_evidence(profile)
    relevant = [item for item in evidence if any(word in item.lower() for word in _job_terms(job.description))]
    if not relevant:
        relevant = evidence[:3]

    lines = [
        f"# Application dossier: {job.company} — {job.title}",
        "",
        f"- Source: [{job.source}]({job.url})",
        f"- Location: {job.location or 'Not stated'}",
        f"- Eligibility: **{ranked.eligibility.status}**",
        f"- Fit score: **{ranked.score}/100**",
        f"- Recommendation: **{ranked.recommendation}**",
        "",
        "## Eligibility evidence",
        "",
        *[f"- {item}" for item in (ranked.eligibility.evidence or ranked.eligibility.reasons)],
        "",
        "## Strongest verified evidence",
        "",
        *[f"- {item}" for item in relevant[:5]],
        "",
        "## Strengths",
        "",
        *[f"- {item}" for item in ranked.strengths],
        "",
        "## Honest gaps or questions",
        "",
        *[f"- {item}" for item in (ranked.gaps or ["No material gap detected by deterministic scoring"])],
        "- Confirm that the company can hire a South African resident without US work authorization.",
        "- Confirm working-hour overlap, employment model, currency, and compensation range.",
        "",
        "## Tailoring brief",
        "",
        "Emphasize Python backend engineering, production automation, APIs, PostgreSQL, Docker, cloud deployment, and measurable operational impact. Use only evidence in the candidate profile. Treat missing requirements as gaps; never invent experience.",
        "The final application artifact should be an ATS-readable PDF. Before generating application text, inspect the live form for restrictions on AI-assisted content. If the employer prohibits it, mark the application as manual_materials_required.",
        "",
        "## Public proof",
        "",
        f"- Portfolio: {profile['portfolio_url']}",
        f"- GitHub: {profile['github_url']}",
        f"- LinkedIn: {profile['linkedin_url']}",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _profile_evidence(profile: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for role in profile.get("experience", []):
        evidence.extend(role.get("evidence", []))
    for project in profile.get("selected_projects", []):
        evidence.extend(project.get("evidence", []))
    evidence.extend(profile.get("professional_evidence", []))
    evidence.extend(profile.get("portfolio_evidence", []))
    return evidence


def _job_terms(description: str) -> set[str]:
    useful = {"python", "django", "fastapi", "api", "postgresql", "docker", "aws", "azure", "react", "typescript", "ai", "llm", "automation", "cloud"}
    lowered = description.lower()
    return {term for term in useful if term in lowered}
