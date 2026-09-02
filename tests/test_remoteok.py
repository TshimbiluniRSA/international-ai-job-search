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
    assert jobs[0].description == "Build FastAPI services. Tags: python api"


def test_does_not_match_keyword_only_in_unrelated_description() -> None:
    payload = [
        {
            "id": "789",
            "company": "Workshop",
            "position": "Wireperson",
            "location": "Southampton",
            "url": "https://remoteok.com/remote-jobs/789",
            "description": "The factory uses automation tools.",
            "tags": ["electrical"],
        }
    ]

    assert normalize_remoteok(payload, ["automation"]) == []


def test_short_ai_keyword_does_not_match_inside_another_word() -> None:
    payload = [
        {
            "id": "999",
            "company": "Airline",
            "position": "Aircraft Maintenance Captain",
            "location": "Panama",
            "url": "https://remoteok.com/remote-jobs/999",
            "description": "Maintain aircraft.",
            "tags": ["captain"],
        }
    ]

    assert normalize_remoteok(payload, ["ai"]) == []
