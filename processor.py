import re
import json
import random
from datetime import datetime
from config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
    AI_BACKEND,
)
from memory import get_recent_context, get_insights, get_suggestions
from task_chains import match_chain, list_chains, execute_chain

OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "llama3.2"

# ─── Fast Pattern Lookup (17k+ patterns) ───
try:
    from patterns_db import PATTERNS
    _PATTERN_SET = set(p.lower() for p in PATTERNS)
    print(f"\033[92m[NLP]\033[0m Loaded {len(_PATTERN_SET):,} offline patterns")
except ImportError:
    _PATTERN_SET = set()
    print(f"\033[93m[NLP]\033[0m patterns_db.py not found - run generate_patterns.py first")


class Context:
    def __init__(self):
        self.last_topic = None
        self.last_action = None
        self.conversation_count = 0
        self.recent_apps = []

    def update(self, topic=None, action=None, app=None):
        if topic:
            self.last_topic = topic
        if action:
            self.last_action = action
        if app:
            self.recent_apps.append(app)
            self.recent_apps = self.recent_apps[-5:]
        self.conversation_count += 1

    def was_recently(self, topic, within=3):
        return self.last_topic == topic and self.conversation_count - self._last_topic_count <= within

    def __init__(self):
        self.last_topic = None
        self.last_action = None
        self.conversation_count = 0
        self.recent_apps = []
        self._last_topic_count = 0

    def update(self, topic=None, action=None, app=None):
        if topic:
            self.last_topic = topic
            self._last_topic_count = self.conversation_count
        if action:
            self.last_action = action
        if app:
            self.recent_apps.append(app)
            self.recent_apps = self.recent_apps[-5:]
        self.conversation_count += 1


_context = Context()


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

        # Try Ollama first (free, local) — quick check with 3s timeout
        try:
            import openai
            import httpx
            test_client = openai.OpenAI(
                api_key="ollama",
                base_url=OLLAMA_BASE_URL,
                timeout=httpx.Timeout(3.0, connect=2.0),
            )
            models = test_client.models.list()
            model_names = [m.id for m in models.data]
            if not model_names:
                print(f"\033[93m[AI]\033[0m Ollama running but no models installed")
            else:
                # Use first available model
                self._model = model_names[0] if model_names else OLLAMA_MODEL
                self._client = test_client
                print(f"\033[92m[AI]\033[0m Ollama connected ({self._model})")
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

        # AI disabled by default to save API balance
        # if self._client and not self._ai_disabled:
        #     result = self._ai_process(text)
        #     if result:
        #         return result

        # Offline chat fallback
        return self._offline_chat(text)

    def _offline_process(self, text):
        # ── Fast lookup: check 17k+ generated patterns first ──
        fast_result = self._fast_pattern_match(text)
        if fast_result:
            return fast_result

        # ── Regex patterns for parameterized commands ──
        patterns = [
            # Task chains
            (r"work mode greeting", lambda t: ("general", "chat", {"text": "Hi Lerito, let's cook!"})),
            (r"work mode music", lambda t: ("general", "work_mode_music", {})),
            (r"run (.+) chain", self._handle_run_chain),
            (r"execute (.+) chain", self._handle_run_chain),
            (r"start (.+) chain", self._handle_run_chain),
            (r"run chain (.+)", self._handle_run_chain),
            (r"list chains", lambda t: ("general", "list_chains", {})),
            (r"what chains", lambda t: ("general", "list_chains", {})),
            (r"suggestions", lambda t: ("general", "get_suggestions", {})),
            (r"what should i do", lambda t: ("general", "get_suggestions", {})),
            # Bot control
            (r"list accounts", lambda t: ("general", "list_accounts", {})),
            (r"show accounts", lambda t: ("general", "list_accounts", {})),
            (r"start bot", lambda t: ("general", "start_bot", {})),
            (r"start trading bot", lambda t: ("general", "start_bot", {})),
            (r"bot status", lambda t: ("general", "bot_status", {})),
            (r"trading bot status", lambda t: ("general", "bot_status", {})),
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
            (r"open (https?://.+)", self._handle_open_url),
            (r"go to (.+)", self._handle_goto),
            # App patterns
            (r"open (.+)", self._handle_open),
            (r"launch (.+)", self._handle_open),
            (r"start (.+)", self._handle_open),
            (r"close all and shut\s*down", lambda t: ("system", "close_all_and_shutdown", {})),
            (r"close all", lambda t: ("system", "close_all", {})),
            (r"quit all", lambda t: ("system", "close_all", {})),
            (r"close (.+)", self._handle_close),
            (r"quit (.+)", self._handle_close),
            (r"kill (.+)", self._handle_close),
            (r"shut\s*down", lambda t: ("system", "shutdown", {})),
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
            # Navigation - mouse
            (r"mouse up", lambda t: ("navigation", "mouse_move_up", {})),
            (r"mouse down", lambda t: ("navigation", "mouse_move_down", {})),
            (r"mouse left", lambda t: ("navigation", "mouse_move_left", {})),
            (r"mouse right", lambda t: ("navigation", "mouse_move_right", {})),
            (r"click", lambda t: ("navigation", "mouse_left_click", {})),
            (r"left click", lambda t: ("navigation", "mouse_left_click", {})),
            (r"right click", lambda t: ("navigation", "mouse_right_click", {})),
            (r"double click", lambda t: ("navigation", "mouse_double_click", {})),
            (r"scroll up", lambda t: ("navigation", "scroll_up", {})),
            (r"scroll down", lambda t: ("navigation", "scroll_down", {})),
            # Navigation - keys
            (r"press up", lambda t: ("navigation", "key_up", {})),
            (r"press down", lambda t: ("navigation", "key_down", {})),
            (r"press left", lambda t: ("navigation", "key_left", {})),
            (r"press right", lambda t: ("navigation", "key_right", {})),
            (r"press enter", lambda t: ("navigation", "key_enter", {})),
            (r"press escape", lambda t: ("navigation", "key_escape", {})),
            (r"press tab", lambda t: ("navigation", "key_tab", {})),
            (r"press space", lambda t: ("navigation", "key_space", {})),
            (r"press backspace", lambda t: ("navigation", "key_backspace", {})),
            (r"press delete", lambda t: ("navigation", "key_delete", {})),
            (r"press home", lambda t: ("navigation", "key_home", {})),
            (r"press end", lambda t: ("navigation", "key_end", {})),
            (r"page up", lambda t: ("navigation", "key_page_up", {})),
            (r"page down", lambda t: ("navigation", "key_page_down", {})),
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

    def _offline_chat(self, text):
        text_clean = text.replace("?", "").replace("!", "").replace(".", "").strip()
        words = text_clean.split()

        # ── Greetings ──
        greetings = ["hello", "hi laura", "hey laura", "hi", "hey", "good morning", "good evening", "good afternoon", "yo", "sup"]
        if any(g in text_clean for g in greetings):
            _context.update(topic="greeting")
            hour = datetime.now().hour
            if hour < 12:
                g = random.choice(["Good morning!", "Morning!", "Hey, good morning!"])
            elif hour < 17:
                g = random.choice(["Good afternoon!", "Hey there!", "Hi!"])
            else:
                g = random.choice(["Good evening!", "Evening!", "Hey!"])
            return ("general", "chat", {"text": f"{g} How can I help you?"})

        # ── How are you ──
        how_are_you = ["how are you", "how you doing", "you good", "you okay", "how do you do"]
        if any(g in text_clean for g in how_are_you):
            _context.update(topic="smalltalk")
            return ("general", "chat", {"text": random.choice([
                "I'm doing great! Ready to help. What do you need?",
                "All systems go! What can I do for you?",
                "Running smoothly! How can I assist you today?",
            ])})

        # ── Farewells ──
        farewells = ["bye", "goodbye", "see you", "later", "goodnight", "good night", "catch you later"]
        if any(f in text_clean for f in farewells):
            _context.update(topic="farewell")
            return ("general", "chat", {"text": random.choice([
                "Goodbye! Have a great day!",
                "See you later! I'll be here if you need me.",
                "Bye! Take care!",
            ])})

        # ── Thanks ──
        thanks = ["thank you", "thanks", "appreciate", "thx", "ty"]
        if any(t in text_clean for t in thanks):
            return ("general", "chat", {"text": random.choice([
                "You're welcome!",
                "Anytime! That's what I'm here for.",
                "No problem at all!",
                "Happy to help!",
            ])})

        # ── Identity ──
        identity = ["who are you", "what are you", "your name", "what's your name", "what is your name"]
        if any(i in text_clean for i in identity):
            return ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, control your laptop, search the web, and keep you company."})

        # ── Capabilities ──
        capabilities = ["what can you do", "what do you do", "help me", "capabilities", "features", "what are your commands"]
        if any(c in text_clean for c in capabilities):
            return ("general", "chat", {"text": "I can open apps, control volume, search the web, manage files, take screenshots, control media, run task chains, and even move your mouse. Just say what you need!"})

        # ── Jokes ──
        joke = ["tell me a joke", "joke", "make me laugh", "be funny", "something funny"]
        if any(j in text_clean for j in joke):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "What's a computer's favorite snack? Microchips!",
                "Why did the computer go to the doctor? Because it had a virus!",
                "I told my computer I needed a break... now it won't stop showing me vacation ads.",
                "Why was the computer cold? It left its Windows open!",
                "What do you call a computer that sings? A-Dell!",
            ]
            return ("general", "chat", {"text": random.choice(jokes)})

        # ── Weather (mock) ──
        if "weather" in text_clean:
            return ("general", "chat", {"text": "I don't have weather data yet, but I can search the web for your local weather. Want me to?"})

        # ── Context-aware follow-ups ──
        if _context.last_topic == "greeting" and any(w in words for w in ["i want", "i need", "can you", "could you", "please"]):
            _context.update(topic="request")
            return ("general", "chat", {"text": "Sure! Tell me what you'd like me to do."})

        if _context.last_topic == "request" and any(w in words for w in ["yes", "yeah", "sure", "okay", "ok"]):
            _context.update(topic="confirmation")
            return ("general", "chat", {"text": "Great! What should I do?"})

        # ── "What about" follow-ups ──
        if text_clean.startswith("what about") or text_clean.startswith("how about"):
            topic = text_clean.replace("what about", "").replace("how about", "").strip()
            if topic:
                _context.update(topic="followup")
                return ("general", "chat", {"text": f"What about {topic}? Can you be more specific?"})

        # ── "Can you" patterns ──
        if text_clean.startswith("can you") or text_clean.startswith("could you") or text_clean.startswith("will you"):
            action = text_clean.replace("can you", "").replace("could you", "").replace("will you", "").strip()
            if action:
                _context.update(topic="request")
                # Try to match the action as a command
                result = self._offline_process(action)
                if result:
                    return result
                return ("general", "chat", {"text": f"I'll try to {action}. Let me see what I can do."})

        # ── "I want to" patterns ──
        if text_clean.startswith("i want to") or text_clean.startswith("i need to"):
            action = text_clean.replace("i want to", "").replace("i need to", "").strip()
            if action:
                _context.update(topic="request")
                result = self._offline_process(action)
                if result:
                    return result
                return ("general", "chat", {"text": f"Okay, I'll help you {action}."})

        # ── "Open" without app name ──
        if text_clean in ["open", "launch", "start"]:
            return ("general", "chat", {"text": "What would you like me to open?"})

        # ── "Close" without app name ──
        if text_clean in ["close", "quit", "exit"]:
            return ("general", "chat", {"text": "What would you like me to close?"})

        # ── Unknown command with context ──
        _context.update(topic="unknown")
        return ("general", "chat", {"text": random.choice([
            "I'm not sure I understand. Can you rephrase that?",
            "I didn't quite get that. Could you say it differently?",
            "Hmm, I'm not sure how to do that yet. Try asking me to open an app or search the web!",
            "I'm still learning. Can you try saying that another way?",
        ])})

    def _ai_process(self, text):
        context = get_recent_context(6)
        insights = get_insights()
        suggestions = get_suggestions()

        system_prompt = f"""You are Laura, a Windows voice assistant with memory and task chains.

Recent conversation:
{context if context else "No recent conversation."}

User patterns: {insights if insights else "No data yet."}
Suggestions: {', '.join(suggestions) if suggestions else "None."}

Parse the user's command and return a JSON object with:
- "module": one of "apps", "system", "web", "files", "media", "general"
- "action": the function to call
- "params": dict of parameters

Available commands:
- apps: open_app(app_name), close_app(app_name)
- system: shutdown(), restart(), lock(), sleep(), hibernate(), cancel_shutdown(), mute(), unmute(), volume_up(), volume_down(), set_volume(level), get_volume(), screenshot()
- web: open_url(url), search_web(query, engine="google"), open_youtube(query=None), open_gmail(), open_website(name), open_google_maps(query=None)
- files: open_file(path), list_files(directory=None), create_folder(name, location=None), create_file(name, location=None), delete_file(path), search_files(query, directory=None)
- media: next_track(), previous_track(), play_pause(), increase_brightness(), decrease_brightness(), set_brightness(level)
- general: get_time(), get_date(), get_day(), calculate(expression), get_system_info(), open_cmd(), open_powershell(), open_explorer(path=None), run_chain(chain_name), list_chains(), get_suggestions(), chat(text)

Task chains you can run: {', '.join(list_chains().keys())}
To run a chain: {{"module": "general", "action": "run_chain", "params": {{"chain_name": "name"}}}}
To list chains: {{"module": "general", "action": "list_chains", "params": {{}}}}
To get suggestions: {{"module": "general", "action": "get_suggestions", "params": {{}}}}

Return ONLY valid JSON. No explanation. Example: {{"module": "apps", "action": "open_app", "params": {{"app_name": "chrome"}}}}
If the command is a greeting or chat, return: {{"module": "general", "action": "chat", "params": {{"text": "your friendly response here"}}}}
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
                    print(f"\033[93m[AI]\033[0m API balance depleted - AI disabled")
                    self._ai_disabled = True
                else:
                    print(f"\033[91m[AI Error]\033[0m {e}")
                continue

        return None

    def _handle_open(self, match):
        app_name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["open", "launch", "start"])
        _context.update(topic="app", action="open", app=app_name)
        return ("apps", "open_app", {"app_name": app_name})

    def _handle_close(self, match):
        app_name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["close", "quit", "kill"])
        _context.update(topic="app", action="close", app=app_name)
        return ("apps", "close_app", {"app_name": app_name})

    def _handle_search(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["search", "search for"])
        query = re.sub(r'^for\s+', '', query)
        _context.update(topic="search")
        return ("web", "search_web", {"query": query})

    def _handle_google(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["google"])
        _context.update(topic="search")
        return ("web", "search_web", {"query": query, "engine": "google"})

    def _handle_youtube(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["youtube"])
        _context.update(topic="media")
        return ("web", "open_youtube", {"query": query})

    def _handle_open_url(self, match):
        url = match.group(1).strip()
        _context.update(topic="web")
        return ("web", "open_url", {"url": url})

    def _handle_goto(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else text_after(match, ["go to"])
        _context.update(topic="web")
        return ("web", "open_website", {"name": name})

    def _handle_open_in_browser(self, match):
        if hasattr(match, 'group') and match.groups():
            query = match.group(1).strip()
        else:
            query = ""
        _context.update(topic="web")
        return ("web", "open_website", {"name": query})

    def _handle_set_volume(self, match):
        level = int(match.group(1))
        _context.update(topic="system")
        return ("system", "set_volume", {"level": level})

    def _handle_calculate(self, match):
        expr = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="math")
        return ("general", "calculate", {"expression": expr})

    def _handle_list_files(self, match):
        directory = match.group(1).strip() if hasattr(match, 'group') and match.groups() else "~\\Desktop"
        _context.update(topic="files")
        return ("files", "list_files", {"directory": directory})

    def _handle_create_folder(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="files")
        return ("files", "create_folder", {"name": name})

    def _handle_create_file(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="files")
        return ("files", "create_file", {"name": name})

    def _handle_open_file(self, match):
        path = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="files")
        return ("files", "open_file", {"filepath": path})

    def _handle_delete(self, match):
        path = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="files")
        return ("files", "delete_file", {"filepath": path})

    def _handle_find_file(self, match):
        query = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="files")
        return ("files", "search_files", {"query": query})

    def _handle_run_chain(self, match):
        name = match.group(1).strip() if hasattr(match, 'group') and match.groups() else ""
        _context.update(topic="chain")
        return ("general", "run_chain", {"chain_name": name})

    def _fast_pattern_match(self, text):
        """Fast lookup in 17k+ generated patterns."""
        if not _PATTERN_SET:
            return None

        text_lower = text.lower().strip()

        # Exact match check (O(1))
        if text_lower in _PATTERN_SET:
            return self._map_pattern_to_action(text_lower)

        # Try stripping common prefixes
        for prefix in ["hey laura", "hi laura", "ok laura", "okay laura", "laura", "computer", "assistant"]:
            if text_lower.startswith(prefix):
                remainder = text_lower[len(prefix):].strip()
                if remainder in _PATTERN_SET:
                    return self._map_pattern_to_action(remainder)

        # Try matching without "please", "can you", etc.
        for prefix in ["please", "can you", "could you", "will you", "would you"]:
            if text_lower.startswith(prefix):
                remainder = text_lower[len(prefix):].strip()
                if remainder in _PATTERN_SET:
                    return self._map_pattern_to_action(remainder)

        return None

    def _map_pattern_to_action(self, pattern):
        """Map a matched pattern string to (module, action, params)."""
        p = pattern.lower()

        # ── System commands (check BEFORE app patterns) ──
        system_map = {
            "shut down": ("system", "shutdown", {}),
            "shutdown": ("system", "shutdown", {}),
            "power off": ("system", "shutdown", {}),
            "turn off the computer": ("system", "shutdown", {}),
            "turn off pc": ("system", "shutdown", {}),
            "restart": ("system", "restart", {}),
            "reboot": ("system", "restart", {}),
            "lock": ("system", "lock", {}),
            "lock the screen": ("system", "lock", {}),
            "sleep": ("system", "sleep", {}),
            "hibernate": ("system", "hibernate", {}),
            "cancel shutdown": ("system", "cancel_shutdown", {}),
            "abort shutdown": ("system", "cancel_shutdown", {}),
            "cancel restart": ("system", "cancel_shutdown", {}),
            "mute": ("system", "mute", {}),
            "unmute": ("system", "unmute", {}),
            "volume up": ("system", "volume_up", {}),
            "turn up the volume": ("system", "volume_up", {}),
            "volume down": ("system", "volume_down", {}),
            "turn down the volume": ("system", "volume_down", {}),
            "screenshot": ("system", "screenshot", {}),
            "take a screenshot": ("system", "screenshot", {}),
        }
        if p in system_map:
            return system_map[p]

        # ── Apps ──
        for phrase in ["open", "launch", "start", "run", "load", "fire up", "boot up", "bring up", "pull up", "show me"]:
            if p.startswith(phrase):
                app = p[len(phrase):].strip()
                if app:
                    _context.update(topic="app", action="open", app=app)
                    return ("apps", "open_app", {"app_name": app})

        for phrase in ["close", "quit", "exit", "kill", "terminate", "end", "stop", "turn off"]:
            if p.startswith(phrase):
                app = p[len(phrase):].strip()
                if app:
                    _context.update(topic="app", action="close", app=app)
                    return ("apps", "close_app", {"app_name": app})

        # ── Media ──
        media_map = {
            "next track": ("media", "next_track", {}),
            "next song": ("media", "next_track", {}),
            "skip track": ("media", "next_track", {}),
            "skip": ("media", "next_track", {}),
            "previous track": ("media", "previous_track", {}),
            "previous song": ("media", "previous_track", {}),
            "go back": ("media", "previous_track", {}),
            "play": ("media", "play_pause", {}),
            "pause": ("media", "play_pause", {}),
            "brightness up": ("media", "increase_brightness", {}),
            "increase brightness": ("media", "increase_brightness", {}),
            "brightness down": ("media", "decrease_brightness", {}),
            "decrease brightness": ("media", "decrease_brightness", {}),
        }
        if p in media_map:
            return media_map[p]

        # ── Navigation ──
        nav_map = {
            "mouse up": ("navigation", "mouse_move_up", {}),
            "mouse down": ("navigation", "mouse_move_down", {}),
            "mouse left": ("navigation", "mouse_move_left", {}),
            "mouse right": ("navigation", "mouse_move_right", {}),
            "click": ("navigation", "mouse_left_click", {}),
            "left click": ("navigation", "mouse_left_click", {}),
            "right click": ("navigation", "mouse_right_click", {}),
            "double click": ("navigation", "mouse_double_click", {}),
            "scroll up": ("navigation", "scroll_up", {}),
            "scroll down": ("navigation", "scroll_down", {}),
            "press up": ("navigation", "key_up", {}),
            "up arrow": ("navigation", "key_up", {}),
            "press down": ("navigation", "key_down", {}),
            "down arrow": ("navigation", "key_down", {}),
            "press left": ("navigation", "key_left", {}),
            "press right": ("navigation", "key_right", {}),
            "press enter": ("navigation", "key_enter", {}),
            "press escape": ("navigation", "key_escape", {}),
            "press tab": ("navigation", "key_tab", {}),
            "press space": ("navigation", "key_space", {}),
            "space bar": ("navigation", "key_space", {}),
            "press backspace": ("navigation", "key_backspace", {}),
            "press delete": ("navigation", "key_delete", {}),
            "press home": ("navigation", "key_home", {}),
            "press end": ("navigation", "key_end", {}),
            "page up": ("navigation", "key_page_up", {}),
            "page down": ("navigation", "key_page_down", {}),
        }
        if p in nav_map:
            return nav_map[p]

        # ── Web ──
        web_map = {
            "gmail": ("web", "open_gmail", {}),
            "open gmail": ("web", "open_gmail", {}),
            "open email": ("web", "open_gmail", {}),
            "open mail": ("web", "open_gmail", {}),
            "check email": ("web", "open_gmail", {}),
            "youtube": ("web", "open_youtube", {"query": None}),
            "open youtube": ("web", "open_youtube", {"query": None}),
        }
        if p in web_map:
            return web_map[p]

        # Search patterns
        search_prefixes = ["search for ", "search ", "look up ", "google ", "find me ", "find ", "what is ", "tell me about "]
        for prefix in search_prefixes:
            if p.startswith(prefix):
                query = p[len(prefix):].strip()
                if query:
                    _context.update(topic="search")
                    return ("web", "search_web", {"query": query})

        # YouTube search
        yt_prefixes = ["youtube ", "open youtube ", "play on youtube ", "search youtube "]
        for prefix in yt_prefixes:
            if p.startswith(prefix):
                query = p[len(prefix):].strip()
                if query:
                    _context.update(topic="media")
                    return ("web", "open_youtube", {"query": query})

        # ── Task chains ──
        chain_names = ["work mode", "wrap up", "quick setup", "relax", "focus mode"]
        for chain in chain_names:
            if chain in p:
                for phrase in ["run ", "start ", "execute ", "begin ", "activate ", "enable "]:
                    if p.startswith(phrase) or p == chain:
                        _context.update(topic="chain")
                        return ("general", "run_chain", {"chain_name": chain})

        # ── File operations ──
        file_map = {
            "list files": ("files", "list_files", {"directory": None}),
            "show files": ("files", "list_files", {"directory": None}),
            "what files": ("files", "list_files", {"directory": None}),
            "show me files": ("files", "list_files", {"directory": None}),
            "list my files": ("files", "list_files", {"directory": None}),
        }
        if p in file_map:
            return file_map[p]

        # ── Time/Date ──
        time_keywords = ["what time", "what's the time", "tell me the time", "time now"]
        if any(t in p for t in time_keywords):
            return ("general", "get_time", {})

        date_keywords = ["what date", "what's the date", "today's date", "date today"]
        if any(d in p for d in date_keywords):
            return ("general", "get_date", {})

        day_keywords = ["what day", "what's the day", "what day is it"]
        if any(d in p for d in day_keywords):
            return ("general", "get_day", {})

        # ── Calculator ──
        calc_prefixes = ["calculate ", "compute ", "what's ", "what is ", "figure out ", "solve "]
        for prefix in calc_prefixes:
            if p.startswith(prefix):
                expr = p[len(prefix):].strip()
                if expr:
                    _context.update(topic="math")
                    return ("general", "calculate", {"expression": expr})

        # ── Chat responses (exact matches) ──
        chat_exact = {
            "who are you": ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."}),
            "what are you": ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."}),
            "your name": ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."}),
            "what's your name": ("general", "chat", {"text": "I'm Laura, your voice assistant. I can open apps, search the web, control volume, and more."}),
            "thank you": ("general", "chat", {"text": "You're welcome!"}),
            "thanks": ("general", "chat", {"text": "You're welcome!"}),
            "tell me a joke": ("general", "chat", {"text": random.choice([
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "What's a computer's favorite snack? Microchips!",
                "Why did the computer go to the doctor? Because it had a virus!",
                "I told my computer I needed a break... now it won't stop showing me vacation ads.",
                "Why was the computer cold? It left its Windows open!",
                "What do you call a computer that sings? A-Dell!",
            ])}),
            "help": ("general", "chat", {"text": "I can open apps, control volume, search the web, manage files, take screenshots, control media, run task chains, and even move your mouse. Just say what you need!"}),
            "commands": ("general", "chat", {"text": "I can open apps, control volume, search the web, manage files, take screenshots, control media, run task chains, and even move your mouse. Just say what you need!"}),
        }
        if p in chat_exact:
            return chat_exact[p]

        # ── Greetings (only if it's a short greeting phrase) ──
        greeting_exact = ["hello", "hi", "hey", "yo", "sup", "hi laura", "hey laura", "yo laura", "good morning", "good afternoon", "good evening"]
        if p in greeting_exact or p.startswith("good morning") or p.startswith("good afternoon") or p.startswith("good evening"):
            _context.update(topic="greeting")
            hour = datetime.now().hour
            if hour < 12:
                g = random.choice(["Good morning!", "Morning!", "Hey, good morning!"])
            elif hour < 17:
                g = random.choice(["Good afternoon!", "Hey there!", "Hi!"])
            else:
                g = random.choice(["Good evening!", "Evening!", "Hey!"])
            return ("general", "chat", {"text": f"{g} How can I help you?"})

        # ── Farewells (only if it's a short farewell phrase) ──
        farewell_exact = ["bye", "goodbye", "see you", "later", "goodnight", "good night", "catch you later", "bye laura", "goodbye laura"]
        if p in farewell_exact or p.startswith("see you") or p.startswith("catch you"):
            _context.update(topic="farewell")
            return ("general", "chat", {"text": random.choice([
                "Goodbye! Have a great day!",
                "See you later! I'll be here if you need me.",
                "Bye! Take care!",
            ])})

        # ── How are you ──
        how_keywords = ["how are you", "how you doing", "you good", "you okay"]
        if any(h in p for h in how_keywords):
            _context.update(topic="smalltalk")
            return ("general", "chat", {"text": random.choice([
                "I'm doing great! Ready to help. What do you need?",
                "All systems go! What can I do for you?",
                "Running smoothly! How can I assist you today?",
            ])})

        # ── Capabilities ──
        cap_keywords = ["what can you do", "what do you do", "capabilities", "features"]
        if any(c in p for c in cap_keywords):
            return ("general", "chat", {"text": "I can open apps, control volume, search the web, manage files, take screenshots, control media, run task chains, and even move your mouse. Just say what you need!"})

        return None


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
