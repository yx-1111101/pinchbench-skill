#!/usr/bin/env python3
"""Fetch and print a weather summary for San Francisco using wttr.in."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

CITY = "San Francisco"
URL = "https://wttr.in/{}?format=j1".format(urllib.parse.quote(CITY))


def fetch_weather(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "weather-summary-script/1.0",
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
    desc = current["weatherDesc"][0]["value"]
    temp_f = current["temp_F"]
    feels_like_f = current["FeelsLikeF"]
    humidity = current["humidity"]
    wind_mph = current["windspeedMiles"]
    high_f = today["maxtempF"]
    low_f = today["mintempF"]

    print(
        f"San Francisco weather: {desc}, {temp_f}°F "
        f"(feels like {feels_like_f}°F). "
        f"Humidity is {humidity}% with winds around {wind_mph} mph. "
        f"Today's high is {high_f}°F and low is {low_f}°F."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
