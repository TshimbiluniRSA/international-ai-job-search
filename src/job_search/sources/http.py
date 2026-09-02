from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "international-ai-job-search/0.2 (+personal, low-volume use)"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class SourceHTTPError(RuntimeError):
    """Raised when a public job source cannot be read safely."""

    def __init__(self, url: str, attempts: int, reason: str) -> None:
        super().__init__(f"Failed to fetch {url} after {attempts} attempt(s): {reason}")
        self.url = url
        self.attempts = attempts
        self.reason = reason


def _retry_delay(error: Exception, attempt: int, backoff: float) -> float:
    if isinstance(error, HTTPError) and error.code == 429:
        retry_after = error.headers.get("Retry-After") if error.headers else None
        if retry_after:
            try:
                return min(float(retry_after), 60.0)
            except ValueError:
                pass
    return backoff * (2 ** (attempt - 1))


def get_json(
    url: str,
    timeout: int = 20,
    attempts: int = 3,
    backoff: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    last_error: Exception | None = None
    used_attempts = 0

    for attempt in range(1, attempts + 1):
        used_attempts = attempt
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as error:
            last_error = error
            if error.code not in RETRYABLE_STATUS_CODES:
                break
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error

        if attempt < attempts:
            sleep(_retry_delay(last_error, attempt, backoff))

    reason = str(last_error) if last_error else "unknown source error"
    raise SourceHTTPError(url, used_attempts, reason) from last_error
