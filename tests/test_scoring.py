from job_search.models import Job
from job_search.scoring import APPLICATION_THRESHOLD, rank_job

PROFILE = {
    "core_skills": ["python", "fastapi", "postgresql", "docker", "aws"],
    "skill_evidence": {"python": ["Production Python APIs"]},
}


def test_matching_global_backend_role_reaches_application_threshold() -> None:
    job = Job(
        "test", "1", "Acme", "Python Backend Engineer", "Remote worldwide", "https://example.com",
        "Build Python FastAPI APIs using PostgreSQL, Docker and AWS. International candidates welcome.",
    )
    result = rank_job(job, PROFILE)
    assert result.eligibility.status == "eligible"
    assert result.score >= APPLICATION_THRESHOLD
    assert result.recommendation == "apply now"
    assert any("Verified evidence" in strength for strength in result.strengths)


def test_matching_plain_remote_role_can_be_ready_to_apply() -> None:
    job = Job(
        "test", "2", "Acme", "Python Backend Engineer", "Remote", "https://example.com/2",
        "Build Python FastAPI APIs using PostgreSQL, Docker and AWS.",
    )
    result = rank_job(job, PROFILE)
    assert result.eligibility.status == "eligible"
    assert result.score >= APPLICATION_THRESHOLD
    assert result.recommendation == "apply now"


def test_score_below_threshold_is_archived() -> None:
    job = Job(
        "test", "3", "Acme", "Python Engineer", "Remote", "https://example.com/3",
        "Build Python services.",
    )
    result = rank_job(job, PROFILE)
    assert result.score < APPLICATION_THRESHOLD
    assert result.recommendation == "archive"


def test_ineligible_role_is_always_zero() -> None:
    job = Job(
        "test", "4", "Acme", "Python Engineer", "Remote US", "https://example.com/4",
        "Python and AWS. US citizenship required.",
    )
    result = rank_job(job, PROFILE)
    assert result.score == 0
    assert result.recommendation == "reject"


def test_senior_role_is_archived_for_early_career_profile() -> None:
    job = Job(
        "test", "5", "Acme", "Senior Python Backend Engineer", "Remote worldwide",
        "https://example.com/5",
        "Build Python FastAPI APIs using PostgreSQL, Docker and AWS.",
    )
    result = rank_job(job, PROFILE)
    assert result.eligibility.status == "eligible"
    assert result.recommendation == "archive"
    assert "Seniority appears above the current primary target" in result.gaps
