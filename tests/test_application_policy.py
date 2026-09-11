from job_search.application_policy import evaluate_application_policy
from job_search.models import Job


def job(description: str) -> Job:
    return Job(
        "test",
        "1",
        "Company",
        "Python Engineer",
        "Remote",
        "https://example.com",
        description,
    )


def test_missing_ai_policy_is_application_ready() -> None:
    result = evaluate_application_policy(job("Build Python APIs for our remote team."))
    assert result.status == "no_ai_restriction_found"
    assert "Prepare truthful" in result.next_action


def test_explicit_ai_restriction_requires_manual_materials() -> None:
    result = evaluate_application_policy(
        job("Candidates must not use generative AI for application responses.")
    )
    assert result.status == "manual_materials_required"
    assert "own words" in result.next_action


def test_explicit_ai_permission_is_application_ready() -> None:
    result = evaluate_application_policy(
        job("AI assistance may be used when preparing application materials.")
    )
    assert result.status == "ai_assistance_allowed"
