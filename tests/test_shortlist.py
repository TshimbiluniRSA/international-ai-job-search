from pathlib import Path

from job_search.models import EligibilityResult, Job, RankedJob
from job_search.shortlist import create_shortlist


def test_shortlist_excludes_archived_jobs(tmp_path: Path) -> None:
    eligible = RankedJob(
        Job("remoteok", "1", "Acme", "Python Engineer", "Worldwide", "https://example.com/1", ""),
        EligibilityResult("eligible"),
        80,
        ["Matching skills: python"],
        [],
        "apply now",
    )
    archived = RankedJob(
        Job("remoteok", "2", "Other", "Designer", "Worldwide", "https://example.com/2", ""),
        EligibilityResult("eligible"),
        20,
        [],
        ["Wrong role"],
        "archive",
    )

    output = create_shortlist([eligible, archived], tmp_path / "shortlist.md")
    text = output.read_text(encoding="utf-8")
    assert "Acme" in text
    assert "Other" not in text
