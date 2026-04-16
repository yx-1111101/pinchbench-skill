#!/usr/bin/env python3
"""Call the API endpoint defined in config.json."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_request(api_config: dict) -> urllib.request.Request:
    endpoint = api_config["endpoint"]
    method = api_config.get("method", "GET").upper()
    headers = api_config.get("headers", {})
    return urllib.request.Request(endpoint, headers=headers, method=method)


def main() -> int:
    config = load_config()
    api_config = config["api"]
    timeout = api_config.get("timeout", 30)
    request = build_request(api_config)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"Status: {response.status}")
            print(body)
        return 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
