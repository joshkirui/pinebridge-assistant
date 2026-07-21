import json
import os
import time
import threading
from datetime import datetime

CHAINS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "task_chains.json")

BUILTIN_CHAINS = {
    "work mode": {
        "description": "Set up full trading/working environment",
        "steps": [
            {"cmd": "close all", "delay": 0},
            {"cmd": "work mode greeting", "delay": 1.5},
            {"cmd": "what time is it", "delay": 3},
            {"cmd": "open tradingview", "delay": 5},
            {"cmd": "open discord", "delay": 6},
            {"cmd": "open unigram", "delay": 7},
            {"cmd": "work mode music", "delay": 8},
        ],
    },
    "wrap up": {
        "description": "Wind down and close everything",
        "steps": [
            {"cmd": "close all", "delay": 0},
            {"cmd": "shutdown in 5 minutes", "delay": 2},
        ],
    },
    "quick setup": {
        "description": "Open essentials fast",
        "steps": [
            {"cmd": "open chrome", "delay": 0},
            {"cmd": "open discord", "delay": 1},
            {"cmd": "open spotify", "delay": 2},
        ],
    },
    "relax": {
        "description": "Set up music and chill",
        "steps": [
            {"cmd": "open spotify", "delay": 0},
            {"cmd": "volume up", "delay": 1},
            {"cmd": "play", "delay": 2},
        ],
    },
    "focus mode": {
        "description": "Minimize distractions",
        "steps": [
            {"cmd": "close discord", "delay": 0},
            {"cmd": "close unigram", "delay": 0.5},
            {"cmd": "close spotify", "delay": 1},
            {"cmd": "open chrome", "delay": 2},
        ],
    },
}


def _load():
    if os.path.exists(CHAINS_FILE):
        try:
            with open(CHAINS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"custom": {}}


def _save(data):
    with open(CHAINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_chain(name):
    name = name.lower().strip()
    if name in BUILTIN_CHAINS:
        return BUILTIN_CHAINS[name]
    data = _load()
    return data.get("custom", {}).get(name)


def list_chains():
    chains = {}
    for name, chain in BUILTIN_CHAINS.items():
        chains[name] = chain["description"]
    data = _load()
    for name, chain in data.get("custom", {}).items():
        chains[name] = chain.get("description", "Custom chain")
    return chains


def save_custom_chain(name, steps, description="Custom chain"):
    data = _load()
    if "custom" not in data:
        data["custom"] = {}
    data["custom"][name.lower().strip()] = {
        "description": description,
        "steps": steps,
    }
    _save(data)


def delete_custom_chain(name):
    data = _load()
    custom = data.get("custom", {})
    name = name.lower().strip()
    if name in custom:
        del custom[name]
        _save(data)
        return True
    return False


def execute_chain(name, emit_fn, speak_fn, delay_factor=1.0):
    chain = get_chain(name)
    if not chain:
        return False, f"Unknown chain: {name}"

    steps = chain.get("steps", [])
    if not steps:
        return False, f"Chain '{name}' has no steps"

    def _run():
        for step in steps:
            delay = step.get("delay", 0) * delay_factor
            cmd = step.get("cmd", "")
            if delay > 0:
                time.sleep(delay)
            emit_fn("command", {"command": cmd})
            print(f"\033[96m[Chain:{name}]\033[0m {cmd}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return True, f"Running '{name}' chain ({len(steps)} steps)"


def match_chain(text):
    text = text.lower().strip()
    for name in BUILTIN_CHAINS:
        if name in text:
            return name
    data = _load()
    for name in data.get("custom", {}):
        if name in text:
            return name
    return None
