"""
utils/internet.py
Handles fetching data from the internet: weather, news, web search.
"""
import requests
import urllib.parse
import system.mac_control as mac

def get_weather(city="New York"):
    """Fetches current weather using a free API (wttr.in)."""
    try:
        # wttr.in is a free, no-key weather API. format=3 gives a short string.
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"The current weather in {response.text}"
        return "I couldn't fetch the weather right now."
    except Exception:
        return "Weather service is currently unreachable."

def search_youtube(query):
    """Constructs a YouTube search URL and opens it."""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    mac.open_website(url)
    return f"Searching YouTube for {query}."

def search_google(query):
    """Constructs a Google search URL and opens it."""
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    mac.open_website(url)
    return f"Searching Google for {query}."
