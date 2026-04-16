#!/usr/bin/env python3
"""Call the API endpoint defined in config.json."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    config = load_config()
    api = config["api"]

    endpoint = api["endpoint"]
    method = api.get("method", "GET")
    headers = api.get("headers", {})
    timeout = api.get("timeout", 30)

    request = Request(endpoint, method=method, headers=headers)

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            print(f"Status: {response.status}")
            print(body)
            return 0
    except HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}")
        if exc.fp is not None:
            print(exc.read().decode("utf-8", errors="replace"))
        return 1
    except URLError as exc:
        print(f"Request failed: {exc.reason}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
