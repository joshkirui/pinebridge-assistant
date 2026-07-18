import re
import json
from config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
    AI_BACKEND,
)

OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "llama3.2"


class Processor:
    def __init__(self):
        self._client = None
        self._model = None
        self._fallback_client = None
        self._fallback_model = None
        self._ai_disabled = False
        self._init_ai()

    def _init_ai(self):
        backend = AI_BACKEND.lower()

        # Try Ollama first (free, local)
        try:
            import openai
            test_client = openai.OpenAI(
                api_key="ollama",
                base_url=OLLAMA_BASE_URL,
            )
            test_client.models.list()
            self._client = test_client
            self._model = OLLAMA_MODEL
            print(f"\033[92m[AI]\033[0m Ollama connected ({OLLAMA_MODEL})")
        except Exception as e:
            print(f"\033[93m[AI]\033[0m Ollama not available: {e}")

        # DeepSeek as fallback
        if DEEPSEEK_API_KEY:
            try:
                import openai
                self._fallback_client = openai.OpenAI(
                    api_key=DEEPSEEK_API_KEY,
                    base_url=DEEPSEEK_BASE_URL,
                )
                self._fallback_model = DEEPSEEK_MODEL
                if not self._client:
                    self._client = self._fallback_client
                    self._model = self._fallback_model
                print(f"\033[92m[AI]\033[0m DeepSeek fallback ready ({DEEPSEEK_MODEL})")
            except Exception as e:
                print(f"\033[91m[AI]\033[0m DeepSeek init failed: {e}")

        # OpenAI as last resort
        if OPENAI_API_KEY and not self._client:
            try:
                import openai
                self._client = openai.OpenAI(api_key=OPENAI_API_KEY)
                self._model = OPENAI_MODEL
                print(f"\033[92m[AI]\033[0m OpenAI connected ({OPENAI_MODEL})")
            except Exception as e:
                print(f"\033[91m[AI]\033[0m OpenAI init failed: {e}")

        if not self._client:
            print(f"\033[93m[AI]\033[0m No AI backend available - offline mode only")

    def process(self, text):
        text = text.lower().strip()
        if not text:
            return None

        # Skip if it's just the wake word or too short
        if len(text.split()) < 2 and text not in ["hello", "hi", "hey", "bye", "yes", "no", "thanks", "yo", "screenshot", "mute", "unmute", "lock", "sleep", "restart", "reboot", "pause", "play", "shutdown"]:
            if text in ["open", "close", "start", "launch"]:
                return ("general", "chat", {"text": "What would you like me to open?"})
            return ("general", "chat", {"text": "Yes? How can I help?"})

        result = self._offline_process(text)
        if result:
            return result

        if self._client and not self._ai_disabled:
            result = self._ai_process(text)
            if result:
                return result

        # Offline chat fallback when AI unavailable
        return self._offline_chat(text)

    def _offline_process(self, text):
        patterns = [
            # Web patterns first (before general open)
            (r"open (.+) in (?:the )?browser", self._handle_open_in_browser),
            (r"open (.+) in chrome", self._handle_open_in_browser),
            (r"open (.+) from chrome", self._handle_open_in_browser),
            (r"open (.+) with chrome", self._handle_open_in_browser),
            (r"browse (.+)", self._handle_open_in_browser),
            (r"navigate to (.+)", self._handle_goto),
            (r"visit (.+)", self._handle_goto),
            (r"search(?: for)? (.+)", self._handle_search),
            (r"google (.+)", self._handle_google),
            (r"youtube (.+)", self._handle_youtube),
            (r"open youtube(?: for)? (.+)", self._handle_youtube),
            (r"open youtube", lambda t: ("web", "open_youtube", {"query": None})),
            (r"open gmail", lambda t: ("web", "open_gmail", {})),
            (r"open email", lambda t: ("web", "open_gmail", {})),
            (r"open mail", lambda t: ("web", "open_gmail", {})),
            (r"go to (.+)", self._handle_goto),
            # App patterns
            (r"open (.+)", self._handle_open),
            (r"launch (.+)", self._handle_open),
            (r"start (.+)", self._handle_open),
            (r"close all", lambda t: ("system", "close_all", {})),
            (r"quit all", lambda t: ("system", "close_all", {})),
            (r"close (.+)", self._handle_close),
            (r"quit (.+)", self._handle_close),
            (r"kill (.+)", self._handle_close),
            (r"shut\s*down", lambda t: ("system", "shutdown", {})),
            (r"close all", lambda t: ("system", "close_all", {})),
            (r"quit all", lambda t: ("system", "close_all", {})),
            (r"restart", lambda t: ("system", "restart", {})),
            (r"reboot", lambda t: ("system", "restart", {})),
            (r"lock", lambda t: ("system", "lock", {})),
            (r"sleep", lambda t: ("system", "sleep", {})),
            (r"hibernate", lambda t: ("system", "hibernate", {})),
            (r"cancel shutdown", lambda t: ("system", "cancel_shutdown", {})),
            (r"cancel restart", lambda t: ("system", "cancel_shutdown", {})),
            (r"unmute", lambda t: ("system", "unmute", {})),
            (r"mute", lambda t: ("system", "mute", {})),
            (r"volume up", lambda t: ("system", "volume_up", {})),
            (r"volume down", lambda t: ("system", "volume_down", {})),
            (r"set volume(?: to)? (\d+)", self._handle_set_volume),
            (r"what(?:'s| is) the volume", lambda t: ("system", "get_volume", {})),
            (r"screenshot", lambda t: ("system", "screenshot", {})),
            (r"take (?:a )?screenshot", lambda t: ("system", "screenshot", {})),
            (r"what time", lambda t: ("general", "get_time", {})),
            (r"what(?:'s| is) the time", lambda t: ("general", "get_time", {})),
            (r"tell me (?:the |what )?time", lambda t: ("general", "get_time", {})),
            (r"what date", lambda t: ("general", "get_date", {})),
            (r"what(?:'s| is) (?:the )?date", lambda t: ("general", "get_date", {})),
            (r"what day", lambda t: ("general", "get_day", {})),
            (r"what(?:'s| is) (?:the )?day", lambda t: ("general", "get_day", {})),
            # Identity/chat patterns (must be before calculator)
            (r"who are you", lambda t: ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."})),
            (r"your name", lambda t: ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."})),
            (r"what(?:'s| is) your name", lambda t: ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."})),
            (r"thank(?:s| you)", lambda t: ("general", "chat", {"text": "You're welcome!"})),
            # Calculator (after identity patterns)
            (r"calculate (.+)", self._handle_calculate),
            (r"compute (.+)", self._handle_calculate),
            (r"what(?:'s| is) (.+)", self._handle_calculate),
            (r"system info", lambda t: ("general", "get_system_info", {})),
            (r"about (?:this )?(?:computer|system|pc)", lambda t: ("general", "get_system_info", {})),
            (r"open (?:command )?(?:prompt|cmd)", lambda t: ("general", "open_cmd", {})),
            (r"open powershell", lambda t: ("general", "open_powershell", {})),
            (r"open (?:file )?explorer", lambda t: ("general", "open_explorer", {"path": None})),
            (r"next track", lambda t: ("media", "next_track", {})),
            (r"next song", lambda t: ("media", "next_track", {})),
            (r"previous (?:track|song)", lambda t: ("media", "previous_track", {})),
            (r"(?:play|pause|toggle)", lambda t: ("media", "play_pause", {})),
            (r"play (?:pause|music)", lambda t: ("media", "play_pause", {})),
            (r"brightness up", lambda t: ("media", "increase_brightness", {})),
            (r"increase brightness", lambda t: ("media", "increase_brightness", {})),
            (r"brightness down", lambda t: ("media", "decrease_brightness", {})),
            (r"decrease brightness", lambda t: ("media", "decrease_brightness", {})),
            (r"list (?:my )?(?:apps|programs|applications)", lambda t: ("apps", "list", {})),
            (r"list files(?: on (?:my )?desktop)?", lambda t: ("files", "list_files", {"directory": "~\\Desktop"})),
            (r"list files in (.+)", self._handle_list_files),
            (r"create (?:a )?folder (?:called )?(.+)", self._handle_create_folder),
            (r"create (?:a )?file (?:called )?(.+)", self._handle_create_file),
            (r"open file (.+)", self._handle_open_file),
            (r"delete (.+)", self._handle_delete),
            (r"find (.+)", self._handle_find_file),
            (r"search (?:for )?files? (.+)", self._handle_find_file),
        ]

        for pattern, handler in patterns:
            match = re.search(pattern, text)
            if match:
                return handler(text if not match.groups() else match)

        return None

    def _ai_process(self, text):
        system_prompt = """You are Laura, a Windows voice assistant. Parse the user's command and return a JSON object with:
- "module": one of "apps", "system", "web", "files", "media", "general"
- "action": the function to call
- "params": dict of parameters

Available commands:
- apps: open_app(app_name), close_app(app_name)
- system: shutdown(), restart(), lock(), sleep(), hibernate(), cancel_shutdown(), mute(), unmute(), volume_up(), volume_down(), set_volume(level), get_volume(), screenshot()
- web: open_url(url), search_web(query, engine="google"), open_youtube(query=None), open_gmail(), open_website(name), open_google_maps(query=None)
- files: open_file(path), list_files(directory=None), create_folder(name, location=None), create_file(name, location=None), delete_file(path), search_files(query, directory=None)
- media: next_track(), previous_track(), play_pause(), increase_brightness(), decrease_brightness(), set_brightness(level)
- general: get_time(), get_date(), get_day(), calculate(expression), get_system_info(), open_cmd(), open_powershell(), open_explorer(path=None)

Return ONLY valid JSON. No explanation. Example: {"module": "apps", "action": "open_app", "params": {"app_name": "chrome"}}
If the command is a greeting or chat, return: {"module": "general", "action": "chat", "params": {"text": "your friendly response here"}}
"""

        # Try primary client, then fallback
        clients = [(self._client, self._model)]
        if self._fallback_client and self._fallback_client is not self._client:
            clients.append((self._fallback_client, self._fallback_model))

        for client, model in clients:
            if not client:
                continue
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1,
                    max_tokens=300
                )
                content = response.choices[0].message.content.strip()
                content = content.replace("```json", "").replace("```", "").strip()
                data = json.loads(content)
                module = data.get("module")
                action = data.get("action")
                params = data.get("params", {})
                if module and action:
                    return (module, action, params)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                err_str = str(e)
                if "402" in err_str or "insufficient" in err_str.lower():
                    print(f"\033[93m[AI]\033[0m API balance depleted")
                    if client is self._client:
                        self._client = self._fallback_client
                        self._model = self._fallback_model
                else:
                    print(f"\033[91m[AI Error]\033[0m {e}")
                continue

        return None

    def _offline_chat(self, text):
        greetings = ["hello", "hi laura", "hey laura", "hi", "hey", "good morning", "good evening", "good afternoon",
                      "how are you", "what's up", "sup", "yo"]
        farewells = ["bye", "goodbye", "see you", "later", "goodnight", "good night"]
        thanks = ["thank you", "thanks", "appreciate"]
        identity = ["who are you", "what are you", "your name", "what's your name", "what is your name"]

        text_clean = text.replace("?", "").replace("!", "").strip()

        if any(i in text_clean for i in identity):
            return ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."})
        if any(g in text_clean for g in greetings):
            return ("general", "chat", {"text": "Hi! I'm Laura. How can I help you?"})
        if any(f in text_clean for f in farewells):
            return ("general", "chat", {"text": "Goodbye! Have a great day!"})
        if any(t in text_clean for t in thanks):
            return ("general", "chat", {"text": "You're welcome!"})

        return None

    def _handle_open(self, match):
        app_name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["open", "launch", "start"])
        return ("apps", "open_app", {"app_name": app_name})

    def _handle_close(self, match):
        app_name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["close", "quit", "kill"])
        return ("apps", "close_app", {"app_name": app_name})

    def _handle_search(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["search", "search for"])
        query = re.sub(r'^for\s+', '', query)
        return ("web", "search_web", {"query": query})

    def _handle_google(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["google"])
        return ("web", "search_web", {"query": query, "engine": "google"})

    def _handle_youtube(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["youtube"])
        return ("web", "open_youtube", {"query": query})

    def _handle_goto(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["go to"])
        return ("web", "open_website", {"name": name})

    def _handle_open_in_browser(self, match):
        if hasattr(match, 'group') and match.groups():
            query = match.group(1).strip()
        else:
            query = ""
        return ("web", "open_website", {"name": query})

    def _handle_set_volume(self, match):
        level = int(match.group(1))
        return ("system", "set_volume", {"level": level})

    def _handle_calculate(self, match):
        expr = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        return ("general", "calculate", {"expression": expr})

    def _handle_list_files(self, match):
        directory = match.group(1).strip() if hasattr(match, 'group') and match.groups() else "~\\Desktop"
        return ("files", "list_files", {"directory": directory})

    def _handle_create_folder(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        return ("files", "create_folder", {"name": name})

    def _handle_create_file(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        return ("files", "create_file", {"name": name})

    def _handle_open_file(self, match):
        path = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        return ("files", "open_file", {"filepath": path})

    def _handle_delete(self, match):
        path = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        return ("files", "delete_file", {"filepath": path})

    def _handle_find_file(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        return ("files", "search_files", {"query": query})


def text_after(match, keywords):
    if isinstance(match, str):
        text = match
    elif hasattr(match, 'group'):
        text = match.group(0)
    else:
        return ""
    for kw in keywords:
        text = re.sub(r'^' + re.escape(kw) + r'\s+', '', text, flags=re.IGNORECASE)
    return text.strip()
