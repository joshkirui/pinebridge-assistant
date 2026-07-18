import os

# Load .env file if it exists
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

WAKE_WORD = "hey laura"
ASSISTANT_NAME = "Laura"

STT_ENGINE = "google"
STT_LANGUAGE = "en-US"

TTS_RATE = 175
TTS_VOLUME = 0.9
TTS_BACKEND = os.environ.get("PINEBRIDGE_TTS", "elevenlabs")
# Options: "elevenlabs", "pyttsx3"

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
# Default female voice: "Rachel" (21m00Tcm4TlvDq8ikWAM)
# Other female voices: "Bella" (EXAVITQu4vr4xnSDxMaL), "Elli" (MF3mGyEYCl7XYWbV3VnO)
# Find more at elevenlabs.io/voice-library or set your custom voice ID

OPENAI_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

AI_BACKEND = os.environ.get("PINEBRIDGE_AI_BACKEND", "deepseek")
# Options: "deepseek", "openai", "none"

COMMAND_TIMEOUT = 10

MIC_MONITOR_ENABLED = True
MIC_MONITOR_STYLE = "bars"
# Options: "bars", "dot", "pulse"

KNOWN_APPS = {
    # Browsers
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "firefox": "start firefox",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    # Office
    "word": r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
    "microsoft word": r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
    "word 2016": r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
    "microsoft excel": r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
    "excel 2016": r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\Office16\POWERPNT.EXE",
    "microsoft powerpoint": r"C:\Program Files\Microsoft Office\Office16\POWERPNT.EXE",
    "powerpoint 2016": r"C:\Program Files\Microsoft Office\Office16\POWERPNT.EXE",
    "outlook": "outlook",
    "microsoft outlook": "outlook",
    "outlook 2016": "outlook",
    "one note": r"C:\Program Files\Microsoft Office\Office16\ONENOTE.EXE",
    "onenote": r"C:\Program Files\Microsoft Office\Office16\ONENOTE.EXE",
    "one note 2016": r"C:\Program Files\Microsoft Office\Office16\ONENOTE.EXE",
    "publisher 2016": r"C:\Program Files\Microsoft Office\Office16\MSPUB.EXE",
    "access 2016": r"C:\Program Files\Microsoft Office\Office16\MSACCESS.EXE",

    # Development
    "vscode": "code",
    "visual studio code": "code",
    "git bash": "bash",
    "git gui": "git-gui",
    "node": "node",
    "node js": "node",
    "python": "python",
    "python 3.11": "python",
    "cursor": r"C:\Users\joshk\AppData\Local\Programs\cursor\Cursor.exe",

    # Media
    "spotify": r"C:\Users\joshk\AppData\Roaming\Spotify\Spotify.exe",
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vlc media player": r"C:\Program Files\VideoLAN\VLC\vlc.exe",

    # Communication
    "discord": r"C:\Users\joshk\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Discord Inc\Discord.lnk",
    "teams": "ms-teams",
    "microsoft teams": "ms-teams",
    "zoom": r"C:\Program Files\Zoom\bin\Zoom.exe",
    "zoom workplace": r"C:\Program Files\Zoom\bin\Zoom.exe",
    "slack": "start slack",
    "skype": "start skype",
    "skype for business": "start lync",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "telegram web": "https://web.telegram.org",
    "unigram": r"shell:AppsFolder\38833FF26BA1D.UnigramPreview_g9c9v27vpyspw!App",
    "snapchat": "https://web.snapchat.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",

    # System Tools
    "notepad": "notepad",
    "paint": "mspaint",
    "calculator": "calc",
    "cmd": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "terminal": "wt",
    "file explorer": "explorer",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "registry editor": "regedit",
    "control panel": "control",
    "settings": "ms-settings:",
    "snipping tool": "snippingtool",
    "remote desktop": "mstsc",
    "remote desktop connection": "mstsc",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "event viewer": "eventvwr",
    "services": "services.msc",
    "system configuration": "msconfig",
    "system information": "msinfo32",
    "resource monitor": "resmon",
    "performance monitor": "perfmon",
    "memory diagnostics": "mdsched",
    "disk cleanup": "cleanmgr",
    "character map": "charmap",
    "steps recorder": "psr",
    "hyper v manager": "virtmgmt.msc",

    # Docker & VMs
    "docker": r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
    "docker desktop": r"C:\Program Files\Docker\Docker\Docker Desktop.exe",

    # Web Apps
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "telegram web": "https://web.telegram.org",
    "tradingview": r"shell:AppsFolder\TradingView.Desktop_n534cwy3pjxzj!App",
    "github": "https://github.com",
    "reddit": "https://reddit.com",
    "amazon": "https://amazon.com",

    # Apps
    "anydesk": r"C:\Program Files (x86)\AnyDesk\AnyDesk.exe",

    # Misc
    "camera": "microsoft.windows.camera:",
    "maps": "bingmaps:",
    "mail": "outlookmail:",
    "weather": "msnweather:",
    "clock": "ms-clock:",
    "alarms": "ms-clock:",
    "calendar": "outlookcal:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "voice access": "voiceaccess",
    "claude": "claude",
}

WEB_SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q=",
    "bing": "https://www.bing.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "youtube": "https://www.youtube.com/results?search_query=",
}

DEFAULT_SEARCH_ENGINE = "google"
