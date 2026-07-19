import ctypes
import ctypes.wintypes
import time

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800

KEYEVENTF_KEYUP = 0x0002

VK_UP = 0x26
VK_DOWN = 0x28
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_TAB = 0x09
VK_SPACE = 0x20
VK_BACK = 0x08
VK_DELETE = 0x2E
VK_HOME = 0x24
VK_END = 0x23
VK_PAGEUP = 0x21
VK_PAGEDOWN = 0x22

user32 = ctypes.windll.user32


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("union", INPUT_UNION)]


def _send_input(*inputs):
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))


def _key_event(vk, flags=0):
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.union.ki.wVk = vk
    inp.union.ki.dwFlags = flags
    _send_input(inp)


def _mouse_event(flags, dx=0, dy=0, data=0):
    inp = INPUT(type=INPUT_MOUSE)
    inp.union.mi.dx = dx
    inp.union.mi.dy = dy
    inp.union.mi.mouseData = data
    inp.union.mi.dwFlags = flags
    _send_input(inp)


def _mouse_move(dx, dy):
    _mouse_event(MOUSEEVENTF_MOVE, dx=dx, dy=dy)


def key_press(vk):
    _key_event(vk, 0)
    _key_event(vk, KEYEVENTF_KEYUP)


# ── Mouse ──────────────────────────────────────────────

def mouse_move_up(pixels=50):
    _mouse_move(0, -pixels)
    return True, "Mouse up"


def mouse_move_down(pixels=50):
    _mouse_move(0, pixels)
    return True, "Mouse down"


def mouse_move_left(pixels=50):
    _mouse_move(-pixels, 0)
    return True, "Mouse left"


def mouse_move_right(pixels=50):
    _mouse_move(pixels, 0)
    return True, "Mouse right"


def mouse_left_click():
    _mouse_event(MOUSEEVENTF_LEFTDOWN)
    _mouse_event(MOUSEEVENTF_LEFTUP)
    return True, "Clicked"


def mouse_right_click():
    _mouse_event(MOUSEEVENTF_RIGHTDOWN)
    _mouse_event(MOUSEEVENTF_RIGHTUP)
    return True, "Right clicked"


def mouse_double_click():
    for _ in range(2):
        _mouse_event(MOUSEEVENTF_LEFTDOWN)
        _mouse_event(MOUSEEVENTF_LEFTUP)
        time.sleep(0.05)
    return True, "Double clicked"


def scroll_up(amount=3):
    _mouse_event(MOUSEEVENTF_WHEEL, data=120 * amount)
    return True, "Scrolled up"


def scroll_down(amount=3):
    _mouse_event(MOUSEEVENTF_WHEEL, data=-120 * amount)
    return True, "Scrolled down"


# ── Keys ───────────────────────────────────────────────

def key_up():
    key_press(VK_UP)
    return True, "Up"


def key_down():
    key_press(VK_DOWN)
    return True, "Down"


def key_left():
    key_press(VK_LEFT)
    return True, "Left"


def key_right():
    key_press(VK_RIGHT)
    return True, "Right"


def key_enter():
    key_press(VK_RETURN)
    return True, "Enter"


def key_escape():
    key_press(VK_ESCAPE)
    return True, "Escape"


def key_tab():
    key_press(VK_TAB)
    return True, "Tab"


def key_space():
    key_press(VK_SPACE)
    return True, "Space"


def key_backspace():
    key_press(VK_BACK)
    return True, "Backspace"


def key_delete():
    key_press(VK_DELETE)
    return True, "Delete"


def key_home():
    key_press(VK_HOME)
    return True, "Home"


def key_end():
    key_press(VK_END)
    return True, "End"


def key_page_up():
    key_press(VK_PAGEUP)
    return True, "Page up"


def key_page_down():
    key_press(VK_PAGEDOWN)
    return True, "Page down"
