#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_request(api_config: dict) -> Request:
    endpoint = api_config["endpoint"]
    method = api_config.get("method", "GET").upper()
    headers = api_config.get("headers", {})
    return Request(endpoint, headers=headers, method=method)


def main() -> int:
    config = load_config(CONFIG_PATH)
    api_config = config["api"]
    timeout = api_config.get("timeout", 30)
    request = build_request(api_config)

    print(f"Endpoint: {api_config['endpoint']}", file=sys.stderr)
    print(f"Method: {api_config.get('method', 'GET').upper()}", file=sys.stderr)

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(body)
        return 0
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        if error_body:
            print(error_body, file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
