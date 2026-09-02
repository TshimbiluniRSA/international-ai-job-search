import json
from pathlib import Path

from job_search.models import EligibilityResult, Job, RankedJob
from job_search.workflow import create_application_queue


def item(recommendation: str) -> RankedJob:
    return RankedJob(
        Job(
            "greenhouse",
            "1",
            "Acme",
            "Python Engineer",
            "Worldwide",
            "https://example.com/1",
            "Python APIs",
        ),
        EligibilityResult("eligible", evidence=["Worldwide"]),
        80,
        ["Matching skills: python"],
        [],
        recommendation,
    )


def test_queue_has_pdf_and_human_approval_gates(tmp_path: Path) -> None:
    destination = tmp_path / "queue.json"
    create_application_queue([item("apply now")], destination)
    payload = json.loads(destination.read_text())

    assert payload["preferred_cv_format"] == "pdf"
    assert payload["submission_mode"] == "human_approved"
    assert payload["items"][0]["required_actions"] == [
        "verify_hiring_location",
        "inspect_application_ai_policy",
        "prepare_truthful_pdf_cv",
        "human_review",
        "approve_final_submission",
        "verify_submission_confirmation",
        "monitor_inbox_feedback",
    ]


def test_queue_excludes_archived_roles(tmp_path: Path) -> None:
    destination = tmp_path / "queue.json"
    create_application_queue([item("archive")], destination)
    payload = json.loads(destination.read_text())
    assert payload["items"] == []
