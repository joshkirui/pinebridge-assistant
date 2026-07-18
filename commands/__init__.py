from commands.apps import open_app, close_app
from commands.system import (
    shutdown, restart, cancel_shutdown, lock_screen,
    sleep_computer, hibernate, get_volume, set_volume,
    volume_up, volume_down, mute, unmute, take_screenshot
)
from commands.web import open_url, search_web, open_youtube, open_gmail, open_website, open_google_maps
from commands.files import open_file, list_files, create_folder, create_file, delete_file, search_files
from commands.media import next_track, previous_track, play_pause, increase_brightness, decrease_brightness
from commands.general import (
    get_time, get_date, get_day, calculate, get_system_info,
    open_cmd, open_powershell, open_explorer
)
