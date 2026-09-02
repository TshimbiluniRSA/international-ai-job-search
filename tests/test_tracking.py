from pathlib import Path

from job_search.models import EligibilityResult, Job, RankedJob
from job_search.tracking import load_tracker, track_job


def ranked_job() -> RankedJob:
    return RankedJob(
        Job("remoteok", "1", "Acme", "Python Engineer", "Worldwide", "https://example.com/1", "Python"),
        EligibilityResult("eligible", evidence=["Worldwide remote"]),
        80,
        ["Matching skills: python"],
        [],
        "apply now",
    )


def test_track_job_adds_then_updates_without_duplicate(tmp_path: Path) -> None:
    tracker = tmp_path / "tracker.json"
    track_job(ranked_job(), tracker, "qualified")
    track_job(ranked_job(), tracker, "applied", "Submitted manually")

    records = load_tracker(tracker)
    assert len(records) == 1
    assert records[0]["status"] == "applied"
    assert records[0]["applied_at"] is not None
    assert records[0]["notes"] == "Submitted manually"
