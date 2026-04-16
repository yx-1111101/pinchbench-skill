#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_config(path: str = "config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    config_path = Path("config.json")
    config = load_config(str(config_path))
    api = config["api"]

    endpoint = api["endpoint"]
    method = api.get("method", "GET").upper()
    headers = api.get("headers", {})
    timeout = api.get("timeout", 30)

    request = Request(endpoint, method=method, headers=headers)

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"Status: {response.status}")
            print(f"Endpoint: {endpoint}")
            print("Response:")
            print(body)
        return 0
    except HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}")
        try:
            print(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            pass
        return 1
    except URLError as exc:
        print(f"Request failed: {exc.reason}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
