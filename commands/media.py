import subprocess
import ctypes


def next_track():
    try:
        import pyautogui
        pyautogui.press("nexttrack")
        return True, "Next track."
    except:
        return False, "Could not control media."


def previous_track():
    try:
        import pyautogui
        pyautogui.press("prevtrack")
        return True, "Previous track."
    except:
        return False, "Could not control media."


def play_pause():
    try:
        import pyautogui
        pyautogui.press("playpause")
        return True, "Play/Pause."
    except:
        return False, "Could not control media."


def stop_media():
    try:
        import pyautogui
        pyautogui.press("stop")
        return True, "Stopped."
    except:
        return False, "Could not control media."


def increase_brightness():
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]
        sbc.set_brightness(min(100, current + 10))
        return True, f"Brightness set to {min(100, current + 10)}%."
    except Exception as e:
        return False, f"Failed to change brightness: {e}"


def decrease_brightness():
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]
        sbc.set_brightness(max(0, current - 10))
        return True, f"Brightness set to {max(0, current - 10)}%."
    except Exception as e:
        return False, f"Failed to change brightness: {e}"


def set_brightness(level):
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        return True, f"Brightness set to {level}%."
    except Exception as e:
        return False, f"Failed to set brightness: {e}"
