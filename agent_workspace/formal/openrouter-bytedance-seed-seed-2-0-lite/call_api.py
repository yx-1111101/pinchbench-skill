#!/usr/bin/env python3
import json
import pathlib
import sys
import urllib.error
import urllib.request

CONFIG_PATH = pathlib.Path(__file__).with_name("config.json")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    config = load_config()
    api = config.get("api", {})

    endpoint = api.get("endpoint")
    method = api.get("method", "GET").upper()
    headers = api.get("headers", {})
    timeout = api.get("timeout", 30)

    if not endpoint:
        print("Error: api.endpoint is missing from config.json", file=sys.stderr)
        return 1

    request = urllib.request.Request(url=endpoint, method=method, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"Status: {response.status}")
            print("Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            print("\nBody:")
            print(body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP Error: {exc.code} {exc.reason}", file=sys.stderr)
        print(error_body, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
