#!/usr/bin/env python3
"""Fetch and print a short weather summary for San Francisco using wttr.in."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


CITY = "San Francisco"
URL = f"https://wttr.in/{urllib.parse.quote(CITY)}?format=j1"


def fetch_weather(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "weather.py/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def main() -> int:
    try:
        data = fetch_weather(URL)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
        return 1

    current = data["current_condition"][0]
    today = data["weather"][0]
    description = current["weatherDesc"][0]["value"]

    print(f"Weather for {CITY}:")
    print(f"- Condition: {description}")
    print(f"- Temperature: {current['temp_C']}°C ({current['temp_F']}°F)")
    print(f"- Feels like: {current['FeelsLikeC']}°C ({current['FeelsLikeF']}°F)")
    print(f"- Humidity: {current['humidity']}%")
    print(f"- Wind: {current['windspeedKmph']} km/h")
    print(
        f"- Today's range: {today['mintempC']}°C to {today['maxtempC']}°C "
        f"({today['mintempF']}°F to {today['maxtempF']}°F)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
