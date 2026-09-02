import io
import json
from urllib.error import HTTPError, URLError

import pytest

from job_search.sources import http


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_get_json_retries_network_error_then_succeeds(monkeypatch) -> None:
    outcomes = iter([URLError("temporary"), Response(b'{"jobs": 2}')])
    delays: list[float] = []

    def open_next(*args, **kwargs):
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(http, "urlopen", open_next)

    result = http.get_json(
        "https://example.com/jobs",
        attempts=3,
        backoff=0.5,
        sleep=delays.append,
    )

    assert result == {"jobs": 2}
    assert delays == [0.5]


def test_get_json_does_not_retry_non_retryable_404(monkeypatch) -> None:
    calls = 0

    def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise HTTPError("https://example.com", 404, "not found", {}, None)

    monkeypatch.setattr(http, "urlopen", fail)

    with pytest.raises(http.SourceHTTPError) as caught:
        http.get_json("https://example.com", attempts=3, sleep=lambda _: None)

    assert calls == 1
    assert caught.value.attempts == 1


def test_get_json_retries_malformed_json(monkeypatch) -> None:
    outcomes = iter([Response(b"{bad json"), Response(json.dumps([1]).encode())])
    monkeypatch.setattr(http, "urlopen", lambda *args, **kwargs: next(outcomes))

    assert http.get_json("https://example.com", attempts=2, sleep=lambda _: None) == [1]
