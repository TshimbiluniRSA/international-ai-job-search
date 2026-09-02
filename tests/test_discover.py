import argparse
import json
from pathlib import Path

from job_search import cli
from job_search.models import Job


def job(source_id: str, url: str, description: str = "Python") -> Job:
    return Job(
        "remoteok",
        source_id,
        "Acme",
        "Python Engineer",
        "Worldwide",
        url,
        description,
        "2026-09-02T00:00:00+00:00",
    )


def write_sources(path: Path, *, greenhouse: bool = False) -> None:
    payload = {
        "greenhouse": (
            [{"company": "Broken", "board_token": "broken"}] if greenhouse else []
        ),
        "lever": [],
        "remoteok": {"enabled": True, "keywords": ["python"]},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_discover_merges_history_and_keeps_successful_sources(tmp_path, monkeypatch) -> None:
    sources = tmp_path / "sources.json"
    output = tmp_path / "jobs.json"
    write_sources(sources, greenhouse=True)
    output.write_text(json.dumps([job("old", "https://example.com/old").to_dict()]))

    monkeypatch.setattr(cli, "fetch_greenhouse", lambda *args: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(cli, "fetch_remoteok", lambda *args: [job("new", "https://example.com/new")])

    status = cli.discover(argparse.Namespace(sources=sources, output=output))
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert status == 0
    assert {item["source_id"] for item in saved} == {"old", "new"}


def test_discover_is_idempotent_and_refreshes_seen_job(tmp_path, monkeypatch) -> None:
    sources = tmp_path / "sources.json"
    output = tmp_path / "jobs.json"
    write_sources(sources)
    output.write_text(
        json.dumps([job("1", "https://example.com/1", "Old description").to_dict()])
    )
    monkeypatch.setattr(
        cli,
        "fetch_remoteok",
        lambda *args: [job("1", "https://example.com/1", "Updated description")],
    )

    assert cli.discover(argparse.Namespace(sources=sources, output=output)) == 0
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert len(saved) == 1
    assert saved[0]["description"] == "Updated description"


def test_discover_preserves_history_when_every_source_fails(tmp_path, monkeypatch) -> None:
    sources = tmp_path / "sources.json"
    output = tmp_path / "jobs.json"
    write_sources(sources)
    original = json.dumps([job("old", "https://example.com/old").to_dict()])
    output.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        cli, "fetch_remoteok", lambda *args: (_ for _ in ()).throw(RuntimeError("down"))
    )

    assert cli.discover(argparse.Namespace(sources=sources, output=output)) == 1
    assert output.read_text(encoding="utf-8") == original
