import os
import json
import time
import subprocess
import threading
from datetime import datetime

ACCOUNTS_FILE = r"C:\Users\joshk\OneDrive\tradingbot\tradingbot\accounts.json"
BOT_DIR = r"C:\Users\joshk\OneDrive\tradingbot\tradingbot"
REMINDER_INTERVAL = 1800

EAT_TIMES = [
    (3, 0, 7, 0),
    (9, 0, 13, 0),
    (16, 30, 18, 0),
    (19, 0, 20, 0),
    (20, 30, 23, 0),
]

_running_bots = {}
_selected_accounts = []
_bot_lock = threading.Lock()


def load_accounts():
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\033[91m[Scheduler]\033[0m Failed to load accounts: {e}")
        return {}


def get_account_list():
    accounts = load_accounts()
    return list(accounts.keys())


def is_eat_time(now):
    h, m = now.hour, now.minute
    current = h * 60 + m
    for sh, sm, eh, em in EAT_TIMES:
        if sh * 60 + sm <= current <= eh * 60 + em:
            return True
    return False


def get_time_label(now):
    h = now.hour
    if h < 12:
        return "morning"
    elif h < 17:
        return "afternoon"
    return "evening"


def start_bot_for_account(account_name):
    with _bot_lock:
        if account_name in _running_bots:
            proc = _running_bots[account_name]
            if proc.poll() is None:
                print(f"\033[93m[Scheduler]\033[0m Bot already running for {account_name}")
                return True

    accounts = load_accounts()
    if account_name not in accounts:
        print(f"\033[91m[Scheduler]\033[0m Account '{account_name}' not found")
        return False

    try:
        bot_script = os.path.join(BOT_DIR, "frost_bot_live.py")
        venv_python = os.path.join(BOT_DIR, ".venv", "Scripts", "python.exe")
        if not os.path.exists(venv_python):
            venv_python = "py"
            cmd = [venv_python, "-3.11", bot_script, account_name]
        else:
            cmd = [venv_python, bot_script, account_name]

        proc = subprocess.Popen(
            cmd,
            cwd=BOT_DIR,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
        )
        with _bot_lock:
            _running_bots[account_name] = proc
        print(f"\033[92m[Scheduler]\033[0m Bot started for {account_name} (PID {proc.pid})")
        return True
    except Exception as e:
        print(f"\033[91m[Scheduler]\033[0m Failed to start bot for {account_name}: {e}")
        return False


def stop_all_bots():
    stopped = []
    with _bot_lock:
        for name, proc in list(_running_bots.items()):
            if proc.poll() is None:
                try:
                    proc.terminate()
                    stopped.append(name)
                except:
                    pass
            del _running_bots[name]
    if stopped:
        print(f"\033[93m[Scheduler]\033[0m Stopped bots: {', '.join(stopped)}")
    return stopped


def stop_bot_for_account(account_name):
    with _bot_lock:
        proc = _running_bots.get(account_name)
        if proc and proc.poll() is None:
            proc.terminate()
            print(f"\033[93m[Scheduler]\033[0m Bot stopped for {account_name}")
            del _running_bots[account_name]
            return True
        elif account_name in _running_bots:
            del _running_bots[account_name]
    return False


def get_bot_status():
    status = {}
    with _bot_lock:
        for name, proc in list(_running_bots.items()):
            if proc.poll() is None:
                status[name] = {"running": True, "pid": proc.pid}
            else:
                status[name] = {"running": False, "exit_code": proc.returncode}
                del _running_bots[name]
    return status


def set_selected_accounts(accounts):
    global _selected_accounts
    _selected_accounts = accounts
    print(f"\033[92m[Scheduler]\033[0m Selected accounts: {', '.join(accounts)}")


def run_scheduler(speaker=None, emit_fn=None):
    last_reminder = 0
    bot_started_windows = set()
    _launched_window = None

    now = datetime.now()
    if is_eat_time(now):
        _launched_window = (now.date(), now.hour)
        print(f"\033[93m[Scheduler]\033[0m Skipping current window (already active at launch)")

    print(f"\033[92m[Scheduler]\033[0m Eating schedule active")
    print(f"  03:00-07:00 | 09:00-13:00 | 16:30-18:00 | 19:00-20:00 | 20:30-23:00")

    while True:
        now = datetime.now()
        today = now.date()

        if is_eat_time(now):
            window_key = (today, now.hour)
            now_ts = time.time()

            if window_key not in bot_started_windows and window_key != _launched_window:
                accounts_to_run = _selected_accounts or get_account_list()
                if accounts_to_run:
                    for acct in accounts_to_run:
                        start_bot_for_account(acct)
                bot_started_windows.add(window_key)

                if speaker:
                    period = get_time_label(now)
                    acct_names = ", ".join(_selected_accounts[:3]) if _selected_accounts else "all accounts"
                    msg = f"Good {period}. Trading bot started for {acct_names}."
                    speaker.say(msg)
                    if emit_fn:
                        emit_fn("response", {"message": msg, "success": True})

            if now_ts - last_reminder >= REMINDER_INTERVAL:
                last_reminder = now_ts
                period = get_time_label(now)
                msg = f"Time to eat, sir. It's {period}."
                print(f"\033[96m[Scheduler]\033[0m {msg}")
                if speaker:
                    speaker.say(msg)
                if emit_fn:
                    emit_fn("response", {"message": msg, "success": True})
        else:
            bot_started_windows.discard((today, now.hour))

        time.sleep(60)


if __name__ == "__main__":
    accounts = get_account_list()
    print("Available accounts:")
    for i, name in enumerate(accounts, 1):
        print(f"  {i}. {name}")
    run_scheduler()
