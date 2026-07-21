from commands.apps import open_app, close_app, list_installed_apps
from commands.system import (
    shutdown, restart, cancel_shutdown, lock_screen,
    sleep_computer, hibernate, get_volume, set_volume,
    volume_up, volume_down, mute, unmute, take_screenshot, close_all, close_all_and_shutdown
)
from commands.web import open_url, search_web, open_youtube, open_gmail, open_website, open_google_maps
from commands.files import open_file, list_files, create_folder, create_file, delete_file, search_files
from commands.media import next_track, previous_track, play_pause, increase_brightness, decrease_brightness
from commands.navigation import (
    mouse_move_up, mouse_move_down, mouse_move_left, mouse_move_right,
    mouse_left_click, mouse_right_click, mouse_double_click,
    scroll_up, scroll_down,
    key_up, key_down, key_left, key_right,
    key_enter, key_escape, key_tab, key_space,
    key_backspace, key_delete, key_home, key_end,
    key_page_up, key_page_down,
)
from commands.general import (
    get_time, get_date, get_day, calculate, get_system_info,
    open_cmd, open_powershell, open_explorer, work_mode_music
)
from memory import get_suggestions as _get_suggestions, get_insights as _get_insights
from task_chains import execute_chain, list_chains as _list_chains


MODULE_MAP = {
    "apps": {
        "open_app": open_app,
        "close_app": close_app,
        "list": lambda **kwargs: (True, "Available apps: " + ", ".join(list_installed_apps()[:20])),
    },
    "system": {
        "shutdown": lambda **kwargs: shutdown(),
        "restart": lambda **kwargs: restart(),
        "cancel_shutdown": lambda **kwargs: cancel_shutdown(),
        "lock": lambda **kwargs: lock_screen(),
        "sleep": lambda **kwargs: sleep_computer(),
        "hibernate": lambda **kwargs: hibernate(),
        "get_volume": lambda **kwargs: (True, f"Volume is at {get_volume()}%."),
        "set_volume": lambda level=50, **kwargs: set_volume(level),
        "volume_up": lambda **kwargs: volume_up(),
        "volume_down": lambda **kwargs: volume_down(),
        "mute": lambda **kwargs: mute(),
        "unmute": lambda **kwargs: unmute(),
        "screenshot": lambda **kwargs: take_screenshot(),
        "close_all": lambda **kwargs: close_all(),
        "close_all_and_shutdown": lambda **kwargs: close_all_and_shutdown(),
    },
    "web": {
        "open_url": lambda url="", **kwargs: open_url(url),
        "search_web": lambda query="", engine="google", **kwargs: search_web(query, engine),
        "open_youtube": lambda query=None, **kwargs: open_youtube(query),
        "open_gmail": lambda **kwargs: open_gmail(),
        "open_website": lambda name="", **kwargs: open_website(name),
        "open_google_maps": lambda query=None, **kwargs: open_google_maps(query),
    },
    "files": {
        "open_file": lambda filepath="", **kwargs: open_file(filepath),
        "list_files": lambda directory=None, **kwargs: list_files(directory),
        "create_folder": lambda name="", location=None, **kwargs: create_folder(name, location),
        "create_file": lambda name="", location=None, **kwargs: create_file(name, location),
        "delete_file": lambda filepath="", **kwargs: delete_file(filepath),
        "search_files": lambda query="", directory=None, **kwargs: search_files(query, directory),
    },
    "media": {
        "next_track": lambda **kwargs: next_track(),
        "previous_track": lambda **kwargs: previous_track(),
        "play_pause": lambda **kwargs: play_pause(),
        "increase_brightness": lambda **kwargs: increase_brightness(),
        "decrease_brightness": lambda **kwargs: decrease_brightness(),
        "set_brightness": lambda level=50, **kwargs: set_brightness(level),
    },
    "navigation": {
        "mouse_move_up": lambda **kwargs: mouse_move_up(),
        "mouse_move_down": lambda **kwargs: mouse_move_down(),
        "mouse_move_left": lambda **kwargs: mouse_move_left(),
        "mouse_move_right": lambda **kwargs: mouse_move_right(),
        "mouse_left_click": lambda **kwargs: mouse_left_click(),
        "mouse_right_click": lambda **kwargs: mouse_right_click(),
        "mouse_double_click": lambda **kwargs: mouse_double_click(),
        "scroll_up": lambda **kwargs: scroll_up(),
        "scroll_down": lambda **kwargs: scroll_down(),
        "key_up": lambda **kwargs: key_up(),
        "key_down": lambda **kwargs: key_down(),
        "key_left": lambda **kwargs: key_left(),
        "key_right": lambda **kwargs: key_right(),
        "key_enter": lambda **kwargs: key_enter(),
        "key_escape": lambda **kwargs: key_escape(),
        "key_tab": lambda **kwargs: key_tab(),
        "key_space": lambda **kwargs: key_space(),
        "key_backspace": lambda **kwargs: key_backspace(),
        "key_delete": lambda **kwargs: key_delete(),
        "key_home": lambda **kwargs: key_home(),
        "key_end": lambda **kwargs: key_end(),
        "key_page_up": lambda **kwargs: key_page_up(),
        "key_page_down": lambda **kwargs: key_page_down(),
    },
    "general": {
        "get_time": lambda **kwargs: get_time(),
        "get_date": lambda **kwargs: get_date(),
        "get_day": lambda **kwargs: get_day(),
        "calculate": lambda expression="", **kwargs: calculate(expression),
        "get_system_info": lambda **kwargs: get_system_info(),
        "open_cmd": lambda **kwargs: open_cmd(),
        "open_powershell": lambda **kwargs: open_powershell(),
        "open_explorer": lambda path=None, **kwargs: open_explorer(path),
        "work_mode_music": lambda **kwargs: work_mode_music(),
        "chat": lambda text="", **kwargs: (True, text),
        "get_suggestions": lambda **kwargs: _handle_suggestions(),
        "list_chains": lambda **kwargs: _handle_list_chains(),
        "run_chain": lambda chain_name="", **kwargs: _handle_run_chain(chain_name),
        "list_accounts": lambda **kwargs: _handle_list_accounts(),
        "start_bot": lambda **kwargs: _handle_start_bot(),
        "stop_bots": lambda **kwargs: _handle_stop_bots(),
        "bot_status": lambda **kwargs: _handle_bot_status(),
    },
}


class Executor:
    def __init__(self):
        self._emit_fn = None
        self._speak_fn = None

    def set_emitters(self, emit_fn, speak_fn):
        self._emit_fn = emit_fn
        self._speak_fn = speak_fn

    def execute(self, command_tuple):
        if command_tuple is None:
            return False, "I didn't understand that command."

        module, action, params = command_tuple

        if module not in MODULE_MAP:
            return False, f"Unknown module: {module}"

        if action not in MODULE_MAP[module]:
            return False, f"Unknown action: {action} in {module}"

        try:
            result = MODULE_MAP[module][action](**params)
            if isinstance(result, tuple) and len(result) == 2:
                return result
            return True, str(result)
        except TypeError as e:
            return False, f"Command error: {e}"
        except Exception as e:
            return False, f"Execution failed: {e}"


_executor_instance = Executor()


def _handle_suggestions():
    suggestions = _get_suggestions()
    if suggestions:
        return True, "Suggestions: " + "; ".join(suggestions)
    return True, "No suggestions right now. Keep using me and I'll learn!"


def _handle_list_chains():
    chains = _list_chains()
    if chains:
        items = [f"  {name}: {desc}" for name, desc in chains.items()]
        return True, "Available chains:\n" + "\n".join(items)
    return True, "No chains available."


def _handle_run_chain(chain_name):
    if not chain_name:
        return False, "Which chain should I run?"
    success, msg = execute_chain(
        chain_name,
        emit_fn=_executor_instance._emit_fn or (lambda *a: None),
        speak_fn=_executor_instance._speak_fn or (lambda *a: None),
    )
    return success, msg


def _handle_list_accounts():
    from scheduler import get_account_list
    accounts = get_account_list()
    if accounts:
        items = [f"  {i}. {name}" for i, name in enumerate(accounts, 1)]
        return True, "Trading accounts:\n" + "\n".join(items)
    return True, "No trading accounts found."


def _handle_start_bot():
    from scheduler import start_bot_for_account, get_account_list
    accounts = get_account_list()
    if not accounts:
        return False, "No trading accounts found."
    started = []
    for acct in accounts:
        if start_bot_for_account(acct):
            started.append(acct)
    if started:
        return True, f"Bot started for: {', '.join(started)}"
    return False, "Failed to start bot."


def _handle_stop_bots():
    from scheduler import stop_all_bots
    stopped = stop_all_bots()
    if stopped:
        return True, f"Stopped bots: {', '.join(stopped)}"
    return True, "No bots were running."


def _handle_bot_status():
    from scheduler import get_bot_status
    status = get_bot_status()
    if status:
        items = []
        for name, info in status.items():
            if info.get("running"):
                items.append(f"  {name}: RUNNING (PID {info.get('pid', '?')})")
            else:
                items.append(f"  {name}: STOPPED")
        return True, "Bot status:\n" + "\n".join(items)
    return True, "No bots currently running."
