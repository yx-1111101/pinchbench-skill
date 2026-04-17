#!/usr/bin/env python3
"""Fetch and print a weather summary for San Francisco using wttr.in."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

API_URL = "https://wttr.in/San%20Francisco?format=j1"
TIMEOUT_SECONDS = 10


def fetch_weather() -> dict:
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "weather-summary-script/1.0"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.load(response)


def build_summary(data: dict) -> str:
    current = data["current_condition"][0]
    today = data["weather"][0]

    description = current["weatherDesc"][0]["value"]
    temperature_f = current["temp_F"]
    feels_like_f = current["FeelsLikeF"]
    humidity = current["humidity"]
    wind_mph = current["windspeedMiles"]
    high_f = today["maxtempF"]
    low_f = today["mintempF"]

    return (
        "San Francisco weather: "
        f"{description}, {temperature_f}°F "
        f"(feels like {feels_like_f}°F). "
        f"High {high_f}°F, low {low_f}°F. "
        f"Humidity {humidity}%. Wind {wind_mph} mph."
    )


def main() -> int:
    try:
        data = fetch_weather()
        print(build_summary(data))
        return 0
    except urllib.error.URLError as exc:
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"Failed to parse weather data: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
