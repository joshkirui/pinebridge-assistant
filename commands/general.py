from datetime import datetime, timezone, timedelta
import math
import subprocess
import os
import time
import threading

WORK_MODE_FILE = r"C:\Users\joshk\Music\8 HOUR R&B MIX 2025 _ SZA Summer Walker Leon Thomas + _ Modern & Throwbacks _ R&B Playlist.m4a"


def _get_forex_sessions():
    now_utc = datetime.now(timezone.utc)
    h = now_utc.hour

    sessions = []
    # Sydney: 9 PM - 6 AM UTC
    if h >= 21 or h < 6:
        sessions.append("Sydney")
    # Tokyo: 12 AM - 9 AM UTC
    if 0 <= h < 9:
        sessions.append("Tokyo")
    # London: 7 AM - 4 PM UTC
    if 7 <= h < 16:
        sessions.append("London")
    # New York: 12 PM - 9 PM UTC
    if 12 <= h < 21:
        sessions.append("New York")

    # Determine market status
    if h in range(21, 24) or h in range(0, 6):
        status = "Asian session"
    elif h in range(7, 12):
        status = "London session"
    elif h in range(12, 16):
        status = "London-New York overlap - most volatile"
    elif h in range(16, 21):
        status = "New York session"
    else:
        status = "Market transitioning"

    return sessions, status


def get_time():
    now = datetime.now()
    sessions, status = _get_forex_sessions()
    time_str = now.strftime('%I:%M %p')
    if sessions:
        session_list = " and ".join(sessions)
        return True, f"It's {time_str}. {status}. {session_list} markets are open."
    return True, f"It's {time_str}."


def get_date():
    now = datetime.now()
    return True, f"Today is {now.strftime('%A, %B %d, %Y')}."


def get_day():
    now = datetime.now()
    return True, f"Today is {now.strftime('%A')}."


def calculate(expression):
    allowed = set("0123456789+-*/.() %")
    expression = expression.lower()
    expression = expression.replace("x", "*").replace("times", "*")
    expression = expression.replace("plus", "+").replace("minus", "-")
    expression = expression.replace("divided by", "/").replace("over", "/")
    expression = expression.replace("power", "**").replace("squared", "**2")
    expression = expression.replace("cubed", "**3")
    expression = expression.replace("square root", "math.sqrt")
    expression = expression.replace("sqrt", "math.sqrt")
    expression = expression.replace("pi", str(math.pi))
    expression = expression.replace("e", str(math.e))

    if not all(c in allowed or c.isalpha() for c in expression):
        return False, "Invalid expression."
    try:
        result = eval(expression, {"__builtins__": {}, "math": math})
        return True, f"The answer is {result}."
    except Exception as e:
        return False, f"Could not calculate: {e}"


def get_system_info():
    import platform
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    processor = platform.processor()
    return True, f"Running {system} {release}, version {version}, {machine} processor."


def open_cmd():
    try:
        subprocess.Popen("cmd", creationflags=subprocess.CREATE_NEW_CONSOLE)
        return True, "Opened Command Prompt."
    except Exception as e:
        return False, f"Failed to open Command Prompt: {e}"


def open_powershell():
    try:
        subprocess.Popen("powershell", creationflags=subprocess.CREATE_NEW_CONSOLE)
        return True, "Opened PowerShell."
    except Exception as e:
        return False, f"Failed to open PowerShell: {e}"


def open_explorer(path=None):
    if path:
        try:
            subprocess.Popen(["explorer", path])
            return True, f"Opened File Explorer at {path}."
        except:
            pass
    try:
        subprocess.Popen("explorer")
        return True, "Opened File Explorer."
    except Exception as e:
        return False, f"Failed to open File Explorer: {e}"


def _move_to_second_screen():
    time.sleep(3)
    ps = 'Add-Type -TypeDefinition "using System; using System.Runtime.InteropServices; public class W { [DllImport(\\"user32.dll\\")] public static extern bool SetWindowPos(IntPtr h,IntPtr a,int x,int y,int cx,int cy,uint f); [DllImport(\\"user32.dll\\")] public static extern IntPtr GetForegroundWindow(); }"; $h=[W]::GetForegroundWindow(); if($h){[W]::SetWindowPos($h,[IntPtr]::Zero,1920,100,1280,720,64)}'
    subprocess.Popen(["powershell", "-Command", ps], creationflags=subprocess.CREATE_NO_WINDOW)


def work_mode_music():
    try:
        os.startfile(WORK_MODE_FILE)
        threading.Thread(target=_move_to_second_screen, daemon=True).start()
        return True, "Playing R&B mix on second screen."
    except Exception as e:
        return False, f"Failed: {e}"
