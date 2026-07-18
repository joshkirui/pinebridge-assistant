import os
import subprocess
import sys
from difflib import get_close_matches


def _fuzzy_match(query, known_apps):
    query = query.lower().strip()
    if query in known_apps:
        return known_apps[query], query

    # Exact prefix match
    for name, cmd in known_apps.items():
        if name.startswith(query):
            return cmd, name

    # Fuzzy match using difflib (handles misspellings)
    matches = get_close_matches(query, known_apps.keys(), n=1, cutoff=0.6)
    if matches:
        return known_apps[matches[0]], matches[0]

    # Partial match fallback
    for name, cmd in known_apps.items():
        if query in name:
            return cmd, name

    return None, query


def open_app(app_name):
    app_name = app_name.lower().strip()
    from config import KNOWN_APPS

    cmd, matched_name = _fuzzy_match(app_name, KNOWN_APPS)
    if cmd:
        try:
            # Windows URIs need "start" command
            if cmd.startswith("http") or cmd.startswith("ms-") or cmd.startswith("bing") or cmd.startswith("microsoft.") or cmd.startswith("outlook") or ":" in cmd:
                os.system(f'start "" "{cmd}"')
            elif cmd.startswith("C:"):
                # Full path - use directly
                subprocess.Popen([cmd], shell=True)
            else:
                # Try direct command first, then with .exe
                try:
                    subprocess.Popen(cmd, shell=True)
                except FileNotFoundError:
                    subprocess.Popen(f"{cmd}.exe", shell=True)
            return True, f"Opening {matched_name}."
        except Exception as e:
            return False, f"Failed to open {matched_name}: {e}"

    # Try start command as last resort
    try:
        os.system(f'start "" "{app_name}"')
        return True, f"Opening {app_name}."
    except Exception as e:
        return False, f"I couldn't find or open {app_name}."


def close_app(app_name):
    app_name = app_name.lower().strip()
    process_map = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "notepad": "notepad.exe",
        "calculator": "Calculator.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "paint": "mspaint.exe",
        "spotify": "Spotify.exe",
        "discord": "Discord.exe",
        "vscode": "Code.exe",
        "visual studio code": "Code.exe",
    }

    process_name = process_map.get(app_name, f"{app_name}.exe")
    try:
        result = subprocess.run(
            ["taskkill", "/IM", process_name, "/F"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return True, f"Closed {app_name}."
        else:
            return False, f"Could not find {app_name} running."
    except Exception as e:
        return False, f"Failed to close {app_name}: {e}"


def list_installed_apps():
    start_menu = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs")
    programs = []
    for root, dirs, files in os.walk(start_menu):
        for f in files:
            if f.endswith(".lnk"):
                programs.append(f.replace(".lnk", ""))
    return programs
