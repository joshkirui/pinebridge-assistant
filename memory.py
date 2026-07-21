import json
import os
import time
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
MAX_HISTORY = 30
MAX_INSIGHTS = 50


def _load():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"history": [], "insights": {}, "chains_used": {}, "first_seen": None}


def _save(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def log_conversation(user_text, laura_response, success=True):
    data = _load()
    if data["first_seen"] is None:
        data["first_seen"] = datetime.now().isoformat()

    entry = {
        "time": datetime.now().isoformat(),
        "user": user_text,
        "laura": laura_response,
        "success": success,
    }
    data["history"].append(entry)
    data["history"] = data["history"][-MAX_HISTORY:]

    _track_patterns(data, user_text)
    _save(data)


def _track_patterns(data, text):
    words = text.lower().split()
    apps = ["chrome", "spotify", "youtube", "discord", "unigram", "tradingview",
            "telegram", "vs code", "cursor", "explorer", "cmd", "powershell"]
    for app in apps:
        if app in text:
            key = f"app_{app}"
            data["insights"][key] = data["insights"].get(key, 0) + 1

    if "open" in words:
        data["insights"]["total_opens"] = data["insights"].get("total_opens", 0) + 1
    if "close" in words:
        data["insights"]["total_closes"] = data["insights"].get("total_closes", 0) + 1

    hour = datetime.now().hour
    period = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
    key = f"time_{period}"
    data["insights"][key] = data["insights"].get(key, 0) + 1

    if len(data["insights"]) > MAX_INSIGHTS:
        oldest = sorted(data["insights"].items(), key=lambda x: x[1])[:5]
        for k, _ in oldest:
            del data["insights"][k]


def log_chain_usage(chain_name):
    data = _load()
    data["chains_used"][chain_name] = data["chains_used"].get(chain_name, 0) + 1
    _save(data)


def get_recent_context(n=10):
    data = _load()
    history = data["history"][-n:]
    lines = []
    for h in history:
        lines.append(f"User: {h['user']}")
        lines.append(f"Laura: {h['laura']}")
    return "\n".join(lines)


def get_insights():
    data = _load()
    insights = data.get("insights", {})
    chains = data.get("chains_used", {})
    first = data.get("first_seen")

    summary = []
    if first:
        days = (datetime.now() - datetime.fromisoformat(first)).days
        summary.append(f"User for {days} days")

    top_apps = sorted(
        [(k.replace("app_", ""), v) for k, v in insights.items() if k.startswith("app_")],
        key=lambda x: x[1], reverse=True
    )[:5]
    if top_apps:
        summary.append("Most used: " + ", ".join(f"{a}({c})" for a, c in top_apps))

    top_chains = sorted(chains.items(), key=lambda x: x[1], reverse=True)[:3]
    if top_chains:
        summary.append("Favorite chains: " + ", ".join(f"{c[0]}({c[1]}x)" for c in top_chains))

    return "; ".join(summary) if summary else "No data yet"


def get_suggestions():
    data = _load()
    insights = data.get("insights", {})
    suggestions = []

    hour = datetime.now().hour
    opens = insights.get("total_opens", 0)
    period = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"

    if hour >= 8 and hour <= 10 and insights.get(f"time_{period}", 0) < 3:
        suggestions.append("Want me to set up your workspace?")

    top_apps = sorted(
        [(k.replace("app_", ""), v) for k, v in insights.items() if k.startswith("app_") and v >= 5],
        key=lambda x: x[1], reverse=True
    )[:3]
    if top_apps and opens > 20:
        names = " and ".join(a for a, _ in top_apps[:2])
        suggestions.append(f"You use {names} a lot. Want shortcuts?")

    return suggestions
