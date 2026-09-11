from pathlib import Path

from job_search.models import EligibilityResult, Job, RankedJob
from job_search.shortlist import create_shortlist


def ranked(
    source_id: str,
    company: str,
    score: int,
    recommendation: str,
    description: str = "",
) -> RankedJob:
    return RankedJob(
        Job(
            "remoteok",
            source_id,
            company,
            "Python Engineer",
            "Remote",
            f"https://example.com/{source_id}",
            description,
        ),
        EligibilityResult("eligible"),
        score,
        ["Matching skills: python"],
        [],
        recommendation,
    )


def test_shortlist_only_includes_apply_now_jobs_at_or_above_70(tmp_path: Path) -> None:
    eligible = ranked("1", "Acme", 70, "apply now")
    below_threshold = ranked("2", "Other", 65, "good match")
    verification = RankedJob(
        Job("remoteok", "3", "Verify", "Backend Engineer", "", "https://example.com/3", ""),
        EligibilityResult("verify"),
        75,
        ["Target role alignment: backend"],
        [],
        "verify hiring location",
    )

    output = create_shortlist(
        [eligible, below_threshold, verification],
        tmp_path / "shortlist.md",
    )
    rendered = output.read_text(encoding="utf-8")
    assert "Acme" in rendered
    assert "Other" not in rendered
    assert "Verify" not in rendered
    assert "at least 70/100" in rendered
    assert "no_ai_restriction_found" in rendered


def test_shortlist_marks_explicit_ai_restriction_as_manual(tmp_path: Path) -> None:
    restricted = ranked(
        "4",
        "Restricted",
        80,
        "apply now",
        "Applicants must not use generative AI for application responses.",
    )

    output = create_shortlist([restricted], tmp_path / "shortlist.md")
    rendered = output.read_text(encoding="utf-8")
    assert "manual_materials_required" in rendered
    assert "Apply manually using only the candidate's own words." in rendered
