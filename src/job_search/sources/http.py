from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


USER_AGENT = "international-ai-job-search/0.1 (+personal, low-volume use)"


def get_json(url: str, timeout: int = 20) -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - configured HTTPS APIs only
        return json.load(response)
