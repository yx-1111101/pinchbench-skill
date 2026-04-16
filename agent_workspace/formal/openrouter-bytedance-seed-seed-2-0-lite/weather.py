#!/usr/bin/env python3
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


CITY = "San Francisco"
URL = "https://wttr.in/{}?format=j1".format(urllib.parse.quote(CITY))


def fetch_weather(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "weather-script/1.0 (+https://wttr.in)"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def main() -> int:
    try:
        data = fetch_weather(URL)
    except urllib.error.URLError as exc:
        print(f"Failed to fetch weather data: {exc}", file=sys.stderr)
        return 1

    current = data["current_condition"][0]
    today = data["weather"][0]
    description = current["weatherDesc"][0]["value"]
    temp_f = current["temp_F"]
    feels_like_f = current["FeelsLikeF"]
    humidity = current["humidity"]
    wind_mph = current["windspeedMiles"]
    high_f = today["maxtempF"]
    low_f = today["mintempF"]

    print(
        f"San Francisco weather: {description}, {temp_f}°F "
        f"(feels like {feels_like_f}°F). Humidity is {humidity}% "
        f"with wind around {wind_mph} mph. Today's high is {high_f}°F "
        f"and low is {low_f}°F."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
