from pathlib import Path

from job_search.models import EligibilityResult, Job, RankedJob
from job_search.tracking import load_tracker, track_job, update_application


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


def test_tracker_records_materials_and_confirmation_metadata(tmp_path: Path) -> None:
    tracker = tmp_path / "tracker.json"
    track_job(
        ranked_job(),
        tracker,
        "materials_ready",
        metadata={"cv_path": "private/applications/acme/cv.pdf", "application_policy": "ai_allowed"},
    )
    update_application(
        tracker,
        "https://example.com/1",
        "confirmation_received",
        metadata={"confirmation_email_id": "message-123", "next_action": "Await response"},
    )

    record = load_tracker(tracker)[0]
    assert record["cv_path"].endswith("cv.pdf")
    assert record["application_policy"] == "ai_allowed"
    assert record["confirmation_email_id"] == "message-123"
    assert record["confirmation_received_at"] is not None
    assert len(record["events"]) == 2


def test_update_requires_an_existing_application(tmp_path: Path) -> None:
    tracker = tmp_path / "tracker.json"
    try:
        update_application(tracker, "https://example.com/missing", "applied")
    except ValueError as error:
        assert "not tracked" in str(error)
    else:
        raise AssertionError("Expected an unknown URL to be rejected")
