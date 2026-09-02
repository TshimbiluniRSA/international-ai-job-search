from datetime import UTC, datetime, timedelta

from job_search.cli import _is_recent
from job_search.models import Job


def job(posted_at: str | None) -> Job:
    return Job("test", "1", "Acme", "Engineer", "Remote", "https://example.com", "", posted_at)


def test_recent_job_is_included() -> None:
    assert _is_recent(job(datetime.now(UTC).isoformat()), 7)


def test_old_job_is_excluded() -> None:
    old = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    assert not _is_recent(job(old), 7)


def test_unknown_date_is_included_for_manual_review() -> None:
    assert _is_recent(job(None), 7)
