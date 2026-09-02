from job_search.eligibility import evaluate_eligibility
from job_search.models import Job


def job(location: str, description: str) -> Job:
    return Job("test", "1", "Company", "Backend Engineer", location, "https://example.com", description)


def test_rejects_explicit_us_authorization_requirement() -> None:
    result = evaluate_eligibility(job("Remote - US", "Must be authorized to work in the United States."))
    assert result.status == "ineligible"


def test_accepts_global_contractor_role() -> None:
    result = evaluate_eligibility(job("Remote", "Remote worldwide. Independent contractor agreement."))
    assert result.status == "eligible"


def test_marks_ambiguous_remote_role_for_verification() -> None:
    result = evaluate_eligibility(job("Remote", "Join our distributed engineering team."))
    assert result.status == "verify"
