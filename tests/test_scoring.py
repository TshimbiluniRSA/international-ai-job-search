from job_search.models import Job
from job_search.scoring import rank_job

PROFILE = {
    "core_skills": ["python", "fastapi", "postgresql", "docker", "aws"],
    "skill_evidence": {"python": ["Production Python APIs"]},
}


def test_matching_global_backend_role_scores_and_is_eligible() -> None:
    job = Job(
        "test", "1", "Acme", "Python Backend Engineer", "Remote worldwide", "https://example.com",
        "Build Python FastAPI APIs using PostgreSQL, Docker and AWS. International candidates welcome.",
    )
    result = rank_job(job, PROFILE)
    assert result.eligibility.status == "eligible"
    assert result.score >= 65
    assert result.recommendation in {"apply now", "good match"}
    assert any("Verified evidence" in strength for strength in result.strengths)


def test_ineligible_role_is_always_zero() -> None:
    job = Job(
        "test", "2", "Acme", "Python Engineer", "Remote US", "https://example.com",
        "Python and AWS. US citizenship required.",
    )
    result = rank_job(job, PROFILE)
    assert result.score == 0
    assert result.recommendation == "reject"
