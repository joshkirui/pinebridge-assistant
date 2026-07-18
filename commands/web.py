import webbrowser
import subprocess
import re
import os
from config import WEB_SEARCH_ENGINES, DEFAULT_SEARCH_ENGINE

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def open_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        if os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, url])
        else:
            webbrowser.open(url)
        return True, "Done."
    except Exception as e:
        return False, f"Failed to open URL: {e}"


def search_web(query, engine=None):
    engine = engine or DEFAULT_SEARCH_ENGINE
    base_url = WEB_SEARCH_ENGINES.get(engine, WEB_SEARCH_ENGINES["google"])
    url = base_url + query.replace(" ", "+")
    try:
        if os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, url])
        else:
            webbrowser.open(url)
        return True, f"Searching {engine} for '{query}'."
    except Exception as e:
        return False, f"Failed to search: {e}"


def open_youtube(query=None):
    if query:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    else:
        url = "https://www.youtube.com"
    try:
        if os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, url])
        else:
            webbrowser.open(url)
        return True, "Opening YouTube." + (f" Searching for '{query}'." if query else "")
    except Exception as e:
        return False, f"Failed to open YouTube: {e}"


def open_gmail():
    return open_url("https://mail.google.com")


def open_google_maps(query=None):
    if query:
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    else:
        url = "https://www.google.com/maps"
    return open_url(url)


def open_website(name):
    sites = {
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "reddit": "https://reddit.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "facebook": "https://facebook.com",
        "instagram": "https://instagram.com",
        "linkedin": "https://linkedin.com",
        "wikipedia": "https://wikipedia.org",
        "amazon": "https://amazon.com",
        "netflix": "https://netflix.com",
        "spotify": "https://open.spotify.com",
        "chatgpt": "https://chat.openai.com",
        "deepseek": "https://chat.deepseek.com",
        "perplexity": "https://perplexity.ai",
        "tradingview": "https://www.tradingview.com",
        "yahoo finance": "https://finance.yahoo.com",
        "coinmarketcap": "https://coinmarketcap.com",
        "coinbase": "https://www.coinbase.com",
        "binance": "https://www.binance.com",
        "medium": "https://medium.com",
        "dev.to": "https://dev.to",
        "notion": "https://www.notion.so",
        "figma": "https://www.figma.com",
        "canva": "https://www.canva.com",
        "trello": "https://trello.com",
        "slack": "https://slack.com",
        "discord": "https://discord.com/app",
        "whatsapp": "https://web.whatsapp.com",
        "telegram": "https://web.telegram.org",
        "chatgpt": "https://chat.openai.com",
        "claude": "https://claude.ai",
        "gemini": "https://gemini.google.com",
        "copilot": "https://copilot.microsoft.com",
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "google docs": "https://docs.google.com",
        "google drive": "https://drive.google.com",
        "google classroom": "https://classroom.google.com",
        "zoom meeting": "https://zoom.us/join",
        "teams meeting": "https://teams.microsoft.com",
        "onedrive": "https://onedrive.live.com",
        "outlook": "https://outlook.live.com",
        "weather": "https://weather.com",
        "news": "https://news.google.com",
        "sports": "https://sports.google.com",
        "translate": "https://translate.google.com",
        "maps": "https://maps.google.com",
        "flights": "https://www.google.com/travel/flights",
        "hotels": "https://www.google.com/travel/hotels",
    }
    name = name.lower().strip()
    if name in sites:
        return open_url(sites[name])
    # Fuzzy match
    from difflib import get_close_matches
    matches = get_close_matches(name, sites.keys(), n=1, cutoff=0.5)
    if matches:
        return open_url(sites[matches[0]])
    return open_url(f"https://www.google.com/search?q={name.replace(' ', '+')}")
