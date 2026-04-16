#!/usr/bin/env python3

import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen


def fetch_weather(city: str) -> str:
    url = f"https://wttr.in/{quote(city)}?format=3"
    with urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8").strip()


def main() -> int:
    city = "San Francisco"

    try:
        summary = fetch_weather(city)
    except HTTPError as exc:
        print(f"Failed to fetch weather data: HTTP {exc.code}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Failed to fetch weather data: {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    print(f"Weather summary for {city}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
