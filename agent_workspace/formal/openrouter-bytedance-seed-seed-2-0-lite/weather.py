#!/usr/bin/env python3
"""Fetch and print a weather summary for San Francisco using wttr.in."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


CITY = "San Francisco"
URL = f"https://wttr.in/{urllib.parse.quote(CITY)}?format=j1"


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=10) as response:
            data = json.load(response)
    except urllib.error.URLError as exc:
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
        return 1

    current = data["current_condition"][0]
    weather = data["weather"][0]
    description = current["weatherDesc"][0]["value"]
    temp_f = current["temp_F"]
    feels_like_f = current["FeelsLikeF"]
    humidity = current["humidity"]
    wind_mph = current["windspeedMiles"]
    high_f = weather["maxtempF"]
    low_f = weather["mintempF"]

    print(
        f"Weather for {CITY}: {description}. "
        f"Currently {temp_f}°F, feels like {feels_like_f}°F. "
        f"Humidity {humidity}%, wind {wind_mph} mph. "
        f"Today's high is {high_f}°F and low is {low_f}°F."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
