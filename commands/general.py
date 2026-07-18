from datetime import datetime
import math
import subprocess


def get_time():
    now = datetime.now()
    return True, f"It's {now.strftime('%I:%M %p')}."


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
