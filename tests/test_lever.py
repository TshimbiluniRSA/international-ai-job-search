from datetime import UTC, datetime

from job_search.sources.lever import normalize_lever


def test_normalize_lever_uses_created_at_epoch_milliseconds() -> None:
    created = datetime(2026, 9, 1, 12, 30, tzinfo=UTC)
    payload = [
        {
            "id": "abc",
            "text": "Python Backend Engineer",
            "hostedUrl": "https://jobs.lever.co/acme/abc",
            "createdAt": int(created.timestamp() * 1000),
            "descriptionPlain": "Build APIs.",
            "lists": [{"content": "<p>Python and PostgreSQL</p>"}],
            "categories": {"location": "Remote"},
        }
    ]

    jobs = normalize_lever(payload, "Acme")

    assert len(jobs) == 1
    assert jobs[0].posted_at == created.isoformat()
    assert jobs[0].description == "Build APIs. Python and PostgreSQL"


def test_normalize_lever_keeps_unknown_date_as_none() -> None:
    jobs = normalize_lever(
        [
            {
                "id": "abc",
                "text": "Engineer",
                "hostedUrl": "https://jobs.lever.co/acme/abc",
                "createdAt": "not-a-timestamp",
                "categories": {},
            }
        ],
        "Acme",
    )

    assert jobs[0].posted_at is None
