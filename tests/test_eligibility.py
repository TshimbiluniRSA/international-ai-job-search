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


def test_does_not_treat_distant_emea_mention_as_remote_eligibility() -> None:
    description = "Remote team. " + ("unrelated text " * 20) + "EMEA sales office."
    result = evaluate_eligibility(job("Remote", description))
    assert result.status == "verify"


def test_hybrid_cloud_does_not_reject_remote_role() -> None:
    result = evaluate_eligibility(
        job("Remote", "Build services across hybrid cloud infrastructure.")
    )
    assert result.status == "verify"


def test_explicit_hybrid_work_rejects_role() -> None:
    result = evaluate_eligibility(
        job("Johannesburg", "This is a hybrid working arrangement with three office days.")
    )
    assert result.status == "ineligible"


def test_accepts_worldwide_job_board_location() -> None:
    result = evaluate_eligibility(
        job("Home based - Worldwide", "Build Python services for a distributed team.")
    )
    assert result.status == "eligible"


def test_rejects_country_specific_remote_location() -> None:
    result = evaluate_eligibility(
        job("Remote, Canada", "Build Python services for a distributed team.")
    )
    assert result.status == "ineligible"


def test_rejects_non_remote_foreign_location() -> None:
    result = evaluate_eligibility(
        job("Bangalore, India", "Build Python services for a distributed team.")
    )
    assert result.status == "ineligible"
