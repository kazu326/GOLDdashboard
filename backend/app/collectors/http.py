from __future__ import annotations

import json
from urllib.request import Request, urlopen


def fetch_text(url: str, timeout: int = 12) -> str:
    request = Request(url, headers={"User-Agent": "GOLDdashboard/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_json(url: str, timeout: int = 12) -> dict:
    return json.loads(fetch_text(url, timeout=timeout))

