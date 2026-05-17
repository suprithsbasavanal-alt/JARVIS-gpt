"""
utils/internet.py  —  JARVIS 3.0 ULTIMATE
Provides weather lookup and browser-search helpers.
"""

import logging
import subprocess
import os

logger = logging.getLogger("JARVIS.utils.internet")

# Set your OpenWeatherMap API key as an env var: OPENWEATHER_KEY
OWM_KEY  = os.getenv("OPENWEATHER_KEY", "")
CITY     = os.getenv("JARVIS_CITY", "London")   # default city


def get_weather() -> str:
    """
    Fetches current weather from OpenWeatherMap.
    Falls back to a DuckDuckGo instant-answer if no API key is set.
    """
    try:
        import requests
        if OWM_KEY:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": CITY, "appid": OWM_KEY, "units": "metric"}
            r = requests.get(url, params=params, timeout=8)
            data = r.json()
            desc  = data["weather"][0]["description"].capitalize()
            temp  = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            return f"Currently in {CITY}: {desc}, {temp:.1f}°C (feels like {feels:.1f}°C)."
        else:
            # Fallback: DuckDuckGo instant answer
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": f"weather {CITY}", "format": "json", "no_html": 1},
                timeout=8
            )
            data = r.json()
            snippet = data.get("AbstractText", "") or data.get("Answer", "")
            return snippet[:200] if snippet else "Weather data not available. Set OPENWEATHER_KEY in your environment."
    except Exception as e:
        logger.error(f"get_weather error: {e}")
        return "Could not fetch weather. Check your internet connection."


def search_google(query: str) -> str:
    """Opens Google Chrome with the given search query."""
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        os.system(f"open '{url}'")
        return f"Searching Google for '{query}'."
    except Exception as e:
        logger.error(f"search_google error: {e}")
        return "Could not open Google."


def search_youtube(query: str) -> str:
    """Opens Chrome with a YouTube search for the given query."""
    try:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        os.system(f"open '{url}'")
        return f"Opening YouTube search for '{query}'."
    except Exception as e:
        logger.error(f"search_youtube error: {e}")
        return "Could not open YouTube."
