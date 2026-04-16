#!/usr/bin/env python3
import json
import urllib.error
import urllib.request
from pathlib import Path


def load_config(path: str = "config.json") -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    config = load_config()
    api = config["api"]

    url = api["endpoint"]
    method = api.get("method", "GET")
    headers = api.get("headers", {})
    timeout = api.get("timeout", 30)

    request = urllib.request.Request(url=url, method=method, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"Status: {response.status}")
            print(body)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}")
        print(exc.read().decode("utf-8", errors="replace"))
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
