#!/usr/bin/env python3
"""Fetch and print a weather summary for San Francisco using wttr.in."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

LOCATION = "San Francisco"
API_URL = f"https://wttr.in/{urllib.parse.quote(LOCATION)}?format=j1"


def main() -> int:
    try:
        with urllib.request.urlopen(API_URL, timeout=10) as response:
            weather = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
        return 1

    current = weather["current_condition"][0]
    area = weather.get("nearest_area", [{}])[0]

    city = area.get("areaName", [{"value": LOCATION}])[0].get("value", LOCATION)
    region = area.get("region", [{"value": ""}])[0].get("value", "")
    country = area.get("country", [{"value": ""}])[0].get("value", "")
    description = current.get("weatherDesc", [{"value": "Unknown"}])[0].get("value", "Unknown")
    temp_f = current.get("temp_F", "?")
    feels_like_f = current.get("FeelsLikeF", "?")
    humidity = current.get("humidity", "?")
    wind_mph = current.get("windspeedMiles", "?")

    location_parts = [part for part in (city, region, country) if part]
    location_label = ", ".join(location_parts) if location_parts else LOCATION

    print(
        f"Weather for {location_label}: {description}, {temp_f}°F "
        f"(feels like {feels_like_f}°F), humidity {humidity}%, wind {wind_mph} mph."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
