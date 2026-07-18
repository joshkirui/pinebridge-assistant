import os
import subprocess
import ctypes
import sys


def shutdown(delay=0):
    try:
        os.system(f"shutdown /s /t {delay}")
        return True, f"Shutting down in {delay} seconds."
    except Exception as e:
        return False, f"Failed to shutdown: {e}"


def restart(delay=0):
    try:
        os.system(f"shutdown /r /t {delay}")
        return True, f"Restarting in {delay} seconds."
    except Exception as e:
        return False, f"Failed to restart: {e}"


def cancel_shutdown():
    try:
        os.system("shutdown /a")
        return True, "Shutdown cancelled."
    except Exception as e:
        return False, f"Failed to cancel shutdown: {e}"


def lock_screen():
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "Screen locked."
    except Exception as e:
        return False, f"Failed to lock screen: {e}"


def sleep_computer():
    try:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return True, "Putting computer to sleep."
    except Exception as e:
        return False, f"Failed to sleep: {e}"


def hibernate():
    try:
        os.system("shutdown /h")
        return True, "Hibernating."
    except Exception as e:
        return False, f"Failed to hibernate: {e}"


_cached_volume = None

def _get_volume():
    global _cached_volume
    if _cached_volume is not None:
        return _cached_volume
    from pycaw.pycaw import AudioUtilities
    # Try default speaker first
    spk = AudioUtilities.GetSpeakers()
    try:
        _cached_volume = spk.EndpointVolume
        return _cached_volume
    except Exception:
        pass
    # Fallback: try all devices
    for dev in AudioUtilities.GetAllDevices():
        try:
            _cached_volume = dev.EndpointVolume
            return _cached_volume
        except Exception:
            continue
    raise RuntimeError("No audio device supports volume control")


def get_volume():
    try:
        vol = _get_volume()
        return int(vol.GetMasterVolumeLevelScalar() * 100)
    except Exception:
        return -1


def set_volume(level):
    level = max(0, min(100, level))
    try:
        vol = _get_volume()
        vol.SetMasterVolumeLevelScalar(level / 100.0, None)
        return True, f"Volume set to {level}%."
    except Exception as e:
        return False, f"Failed to set volume: {e}"


def volume_up():
    current = get_volume()
    if current >= 0:
        return set_volume(min(100, current + 10))
    return False, "Could not get current volume."


def volume_down():
    current = get_volume()
    if current >= 0:
        return set_volume(max(0, current - 10))
    return False, "Could not get current volume."


def mute():
    try:
        vol = _get_volume()
        vol.SetMute(1, None)
        return True, "Muted."
    except Exception as e:
        return False, f"Failed to mute: {e}"


def unmute():
    try:
        vol = _get_volume()
        vol.SetMute(0, None)
        return True, "Unmuted."
    except Exception as e:
        return False, f"Failed to unmute: {e}"


def take_screenshot():
    import pyautogui
    from datetime import datetime
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(desktop, filename)
    try:
        pyautogui.screenshot(filepath)
        return True, f"Screenshot saved to {filename} on your Desktop."
    except Exception as e:
        return False, f"Failed to take screenshot: {e}"
