from job_search.sources.remoteok import normalize_remoteok


def test_normalizes_and_filters_remoteok_payload() -> None:
    payload = [
        {"legal": "feed metadata"},
        {
            "id": "123",
            "company": "Acme",
            "position": "Python Backend Engineer",
            "location": "Worldwide",
            "url": "https://remoteok.com/remote-jobs/123",
            "description": "<p>Build FastAPI services.</p>",
            "tags": ["python", "api"],
            "date": "2026-09-02",
        },
        {
            "id": "456",
            "company": "Other",
            "position": "Product Designer",
            "location": "Worldwide",
            "url": "https://remoteok.com/remote-jobs/456",
            "description": "Design product interfaces.",
            "tags": ["design"],
        },
    ]

    jobs = normalize_remoteok(payload, ["python", "backend"])

    assert len(jobs) == 1
    assert jobs[0].company == "Acme"
    assert jobs[0].description == "Build FastAPI services."
