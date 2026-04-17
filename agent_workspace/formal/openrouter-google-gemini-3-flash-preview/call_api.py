#!/usr/bin/env python3
"""Simple client for the API endpoint defined in config.json."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    config = load_config()
    api = config.get("api", {})
    endpoint = api.get("endpoint")
    method = api.get("method", "GET")
    headers = api.get("headers", {})
    timeout = api.get("timeout", 30)

    if not endpoint:
        print("Missing api.endpoint in config.json", file=sys.stderr)
        return 1

    request = urllib.request.Request(endpoint, method=method, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"Status: {response.status}")
            print(body)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        body = exc.read().decode("utf-8", errors="replace")
        if body:
            print(body, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
