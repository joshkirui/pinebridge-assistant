from commands.apps import open_app, close_app, list_installed_apps
from commands.system import (
    shutdown, restart, cancel_shutdown, lock_screen,
    sleep_computer, hibernate, get_volume, set_volume,
    volume_up, volume_down, mute, unmute, take_screenshot, close_all, close_all_and_shutdown
)
from commands.web import open_url, search_web, open_youtube, open_gmail, open_website, open_google_maps
from commands.files import open_file, list_files, create_folder, create_file, delete_file, search_files
from commands.media import next_track, previous_track, play_pause, increase_brightness, decrease_brightness
from commands.general import (
    get_time, get_date, get_day, calculate, get_system_info,
    open_cmd, open_powershell, open_explorer
)


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
    "general": {
        "get_time": lambda **kwargs: get_time(),
        "get_date": lambda **kwargs: get_date(),
        "get_day": lambda **kwargs: get_day(),
        "calculate": lambda expression="", **kwargs: calculate(expression),
        "get_system_info": lambda **kwargs: get_system_info(),
        "open_cmd": lambda **kwargs: open_cmd(),
        "open_powershell": lambda **kwargs: open_powershell(),
        "open_explorer": lambda path=None, **kwargs: open_explorer(path),
        "chat": lambda text="", **kwargs: (True, text),
    },
}


class Executor:
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
