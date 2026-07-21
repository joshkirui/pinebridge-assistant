#!/usr/bin/env python3
"""
Generate 10,000+ offline patterns for Laura's NLP.
Run once: py -3.11 generate_patterns.py
Then import generated_patterns in processor.py
"""

import os
import json
from itertools import product

# ─── Pattern Categories ───

WAKE_WORDS = ["laura", "hey laura", "hi laura", "ok laura", "okay laura", "lisa", "hey lisa", "computer", "assistant", "jarvis"]

# App names (common Windows apps)
APPS = [
    "chrome", "google chrome", "firefox", "edge", "microsoft edge", "opera",
    "spotify", "discord", "slack", "teams", "zoom", "skype", "telegram",
    "whatsapp", "notepad", "notepad++", "vs code", "visual studio code", "cursor",
    "word", "microsoft word", "excel", "microsoft excel", "powerpoint", "microsoft powerpoint",
    "outlook", "thunderbird", "file explorer", "explorer", "cmd", "command prompt",
    "powershell", "terminal", "task manager", "control panel", "settings", "calculator",
    "paint", "photoshop", "lightroom", "premiere", "after effects", "figma",
    "blender", "unity", "unreal", "steam", "epic games", "battle.net",
    "vlc", "media player", "itunes", "netflix", "hulu", "disney+",
    "onedrive", "google drive", "dropbox", "github", "gitkraken", "postman",
    "obs", "obs studio", "streamlabs", "audacity", "garageband",
    "tradingview", "mt4", "mt5", "thinkorswim", "robinhood", "coinbase",
    "vpn", "nordvpn", "expressvpn", "windscribe",
    "photos", "camera", "maps", "weather", "clock", "calendar",
    "wordpad", "snipping tool", "magnifier", "narrator",
    "unigram", "telegram desktop",
]

# Opening phrases
OPEN_PHRASES = ["open", "launch", "start", "run", "load", "fire up", "boot up", "bring up", "pull up", "show me", "can you open", "could you open", "please open", "i need", "i want", "get me", "switch to"]
CLOSE_PHRASES = ["close", "quit", "exit", "kill", "shut down", "shut", "terminate", "end", "stop", "turn off"]
SYSTEM_PHRASES = ["", "please", "can you", "could you", "hey laura", "ok laura"]

# System commands
SYSTEM_CMDS = [
    ("shutdown", ["shut down", "shutdown", "power off", "turn off the computer", "turn off pc", "shut down the pc", "shut the computer down"]),
    ("restart", ["restart", "reboot", "restart the computer", "reboot the pc", "restart my computer"]),
    ("lock", ["lock", "lock the screen", "lock my computer", "lock the pc", "lock this computer"]),
    ("sleep", ["sleep", "put to sleep", "sleep mode", "go to sleep", "put the computer to sleep"]),
    ("hibernate", ["hibernate", "hibernation mode", "hibernate the computer"]),
    ("cancel_shutdown", ["cancel shutdown", "cancel the shutdown", "abort shutdown", "stop shutdown", "cancel restart", "abort restart"]),
    ("mute", ["mute", "mute the volume", "mute the sound", "mute audio", "silence", "silence the volume"]),
    ("unmute", ["unmute", "unmute the volume", "unmute the sound", "unmute audio", "unmute the speakers"]),
    ("volume_up", ["volume up", "turn up the volume", "increase volume", "louder", "turn it up", "make it louder", "up the volume"]),
    ("volume_down", ["volume down", "turn down the volume", "decrease volume", "quieter", "turn it down", "make it quieter", "lower the volume", "down the volume"]),
    ("screenshot", ["screenshot", "take a screenshot", "take screenshot", "capture screen", "screen capture", "grab the screen", "snap the screen"]),
]

# Web actions
WEB_ACTIONS = [
    ("search_web", "search for", ["search for", "search", "look up", "google", "find me", "find", "look for", "what is", "tell me about"]),
    ("open_youtube", "youtube", ["youtube", "open youtube", "play on youtube", "search youtube", "youtube search"]),
    ("open_gmail", "gmail", ["gmail", "open gmail", "open email", "open mail", "check email", "check mail", "my email"]),
    ("open_website", "website", ["open website", "go to website", "visit website", "navigate to website"]),
]

# Search topics
SEARCH_TOPICS = [
    "weather", "news", "stocks", "crypto", "bitcoin", "ethereum", "forex",
    "recipes", "restaurants", "hotels", "flights", "movies", "music",
    "sports", "football", "basketball", "soccer", "tennis",
    "python tutorial", "javascript tutorial", "coding", "programming",
    "ai news", "machine learning", "deep learning",
    "best laptops", "best phones", "best headphones",
    "how to cook", "how to code", "how to fix", "how to make",
    "diet plan", "workout", "exercise", "yoga",
    "investment", "trading", "forex pairs", "gold price",
    "netflix shows", "youtube tutorials", "spotify playlists",
]

# Media commands
MEDIA_CMDS = [
    ("next_track", ["next track", "next song", "skip track", "skip song", "skip", "next"]),
    ("previous_track", ["previous track", "previous song", "go back", "go back a song", "last track", "previous"]),
    ("play_pause", ["play", "pause", "toggle play", "play or pause", "resume", "unpause"]),
    ("increase_brightness", ["brightness up", "increase brightness", "brighter", "turn up brightness", "make it brighter"]),
    ("decrease_brightness", ["brightness down", "decrease brightness", "dimmer", "turn down brightness", "make it dimmer", "dim the screen"]),
]

# Navigation commands
NAV_CMDS = [
    ("mouse_move_up", ["mouse up", "move mouse up", "cursor up"]),
    ("mouse_move_down", ["mouse down", "move mouse down", "cursor down"]),
    ("mouse_move_left", ["mouse left", "move mouse left", "cursor left"]),
    ("mouse_move_right", ["mouse right", "move mouse right", "cursor right"]),
    ("mouse_left_click", ["click", "left click", "mouse click", "click here", "tap"]),
    ("mouse_right_click", ["right click", "context menu", "right mouse click"]),
    ("mouse_double_click", ["double click", "double tap", "double click here"]),
    ("scroll_up", ["scroll up", "scroll page up", "page up scroll"]),
    ("scroll_down", ["scroll down", "scroll page down", "page down scroll"]),
    ("key_up", ["press up", "up arrow", "arrow up"]),
    ("key_down", ["press down", "down arrow", "arrow down"]),
    ("key_left", ["press left", "left arrow", "arrow left"]),
    ("key_right", ["press right", "right arrow", "arrow right"]),
    ("key_enter", ["press enter", "enter key", "hit enter", "return key"]),
    ("key_escape", ["press escape", "escape key", "press esc", "esc key"]),
    ("key_tab", ["press tab", "tab key", "hit tab"]),
    ("key_space", ["press space", "space bar", "hit space", "space key"]),
    ("key_backspace", ["press backspace", "backspace key", "delete last character"]),
    ("key_delete", ["press delete", "delete key", "delete character"]),
    ("key_home", ["press home", "home key"]),
    ("key_end", ["press end", "end key"]),
    ("key_page_up", ["page up", "press page up"]),
    ("key_page_down", ["page down", "press page down"]),
]

# Task chains
CHAINS = ["work mode", "wrap up", "quick setup", "relax", "focus mode"]
CHAIN_PHRASES = ["run", "start", "execute", "begin", "activate", "enable", "switch to"]

# Greeting variations
GREETINGS_TIME = {
    "morning": ["good morning", "morning", "morning laura", "good morning laura", "gm", "gm laura"],
    "afternoon": ["good afternoon", "afternoon", "afternoon laura", "good afternoon laura"],
    "evening": ["good evening", "evening", "evening laura", "good evening laura"],
    "night": ["good night", "night", "night laura", "good night laura", "gn"],
}

GREETINGS通用 = ["hello", "hi", "hey", "yo", "sup", "what's up", "howdy", "hiya", "heya", "hello laura", "hi laura", "hey laura", "yo laura", "sup laura"]

# Farewell variations
FAREWELLS = [
    "bye", "goodbye", "see you", "see you later", "catch you later", "talk to you later",
    "gotta go", "i'm leaving", "i'm out", "peace", "later", "cya", "ttyl",
    "bye laura", "goodbye laura", "see you laura", "later laura",
    "have a good one", "take care", "have a great day", "have a nice day",
]

# Thanks variations
THANKS = [
    "thank you", "thanks", "appreciate", "thx", "ty", "tysm", "thank you so much",
    "thanks a lot", "thanks laura", "thank you laura", "appreciate it",
    "much appreciated", "you're the best", "you're amazing", "great job",
    "nice work", "well done", "perfect", "awesome", "brilliant",
]

# How are you variations
HOW_ARE_YOU = [
    "how are you", "how are you doing", "how you doing", "you good",
    "you okay", "how do you do", "how's it going", "how's everything",
    "how have you been", "what's up with you", "how's life",
    "how are things", "you doing okay", "everything good",
]

# Identity questions
IDENTITY = [
    "who are you", "what are you", "your name", "what's your name",
    "what is your name", "who am i talking to", "who am i speaking to",
    "tell me about yourself", "introduce yourself", "what should i call you",
    "what are you called", "are you an ai", "are you a robot",
    "are you human", "are you real",
]

# Capability questions
CAPABILITIES = [
    "what can you do", "what do you do", "help me", "capabilities",
    "features", "what are your commands", "what are you able to do",
    "what can laura do", "show me what you can do", "how can you help",
    "what services do you provide", "what can i ask you",
    "what kind of things can you do", "give me a list of commands",
    "help", "commands", "menu",
]

# Jokes
JOKES = [
    "tell me a joke", "joke", "make me laugh", "be funny",
    "something funny", "tell me something funny", "say something funny",
    "make me smile", "entertain me", "humor me",
]

# Weather
WEATHER = ["weather", "what's the weather", "how's the weather", "is it raining", "is it sunny", "temperature", "forecast"]

# Time/Date
TIME_PATTERNS = ["what time", "what's the time", "what is the time", "tell me the time", "what time is it", "current time", "time now"]
DATE_PATTERNS = ["what date", "what's the date", "what is the date", "what's today", "today's date", "current date", "date today", "what day is it", "what day", "what's the day"]

# Calculator
CALC_PREFIXES = ["calculate", "compute", "what's", "what is", "figure out", "solve", "do the math for"]
CALC_EXAMPLES = ["2 plus 2", "10 minus 5", "6 times 7", "100 divided by 4", "square root of 16", "5 squared", "2 to the power of 10"]

# File operations
FILE_OPS = [
    ("list_files", ["list files", "show files", "what files", "show me files", "list my files", "what's on my desktop", "show desktop files"]),
    ("create_folder", ["create folder", "make folder", "new folder", "create a folder", "make a new folder"]),
    ("create_file", ["create file", "make file", "new file", "create a file", "make a new file"]),
    ("open_file", ["open file", "open the file", "show me the file"]),
    ("delete_file", ["delete file", "remove file", "delete the file", "remove the file"]),
    ("search_files", ["find file", "search for file", "find the file", "locate file", "where is my file"]),
]

# Conversational fillers
FILLERS = ["um", "uh", "let me think", "hmm", "okay so", "right", "so", "well"]

# Confirmations
CONFIRMATIONS = ["yes", "yeah", "sure", "okay", "ok", "yep", "yup", "alright", "right", "correct", "that's right", "exactly"]

# Negations
NEGATIONS = ["no", "nope", "nah", "not really", "no thanks", "i'm good", "pass", "never mind", "cancel", "forget it"]

# ─── Generate Patterns ───

def generate_app_patterns():
    """Generate open/close patterns for all apps with all phrase variations."""
    patterns = []
    for app in APPS:
        for phrase in OPEN_PHRASES:
            # Basic: "open chrome"
            patterns.append(f"{phrase} {app}")
            # With prefix: "please open chrome"
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {phrase} {app}")
        for phrase in CLOSE_PHRASES:
            patterns.append(f"{phrase} {app}")
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {phrase} {app}")
    return patterns


def generate_system_patterns():
    """Generate system command patterns."""
    patterns = []
    for action, variations in SYSTEM_CMDS:
        for v in variations:
            patterns.append(v)
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {v}")
    return patterns


def generate_web_patterns():
    """Generate web search patterns."""
    patterns = []
    for action, base, phrases in WEB_ACTIONS:
        for phrase in phrases:
            patterns.append(phrase)
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {phrase}")
    # Add search topics
    for topic in SEARCH_TOPICS:
        patterns.append(f"search for {topic}")
        patterns.append(f"google {topic}")
        patterns.append(f"look up {topic}")
        patterns.append(f"find {topic}")
        patterns.append(f"what is {topic}")
        patterns.append(f"tell me about {topic}")
        for prefix in SYSTEM_PHRASES:
            if prefix:
                patterns.append(f"{prefix} search for {topic}")
                patterns.append(f"{prefix} google {topic}")
    return patterns


def generate_media_patterns():
    """Generate media command patterns."""
    patterns = []
    for action, variations in MEDIA_CMDS:
        for v in variations:
            patterns.append(v)
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {v}")
    return patterns


def generate_nav_patterns():
    """Generate navigation command patterns."""
    patterns = []
    for action, variations in NAV_CMDS:
        for v in variations:
            patterns.append(v)
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {v}")
    return patterns


def generate_chain_patterns():
    """Generate task chain patterns."""
    patterns = []
    for chain in CHAINS:
        for phrase in CHAIN_PHRASES:
            patterns.append(f"{phrase} {chain}")
            patterns.append(f"{phrase} {chain} chain")
            patterns.append(f"run {chain}")
            patterns.append(f"start {chain}")
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {phrase} {chain}")
    return patterns


def generate_greeting_patterns():
    """Generate greeting patterns."""
    patterns = []
    for period, greetings in GREETINGS_TIME.items():
        for g in greetings:
            patterns.append(g)
    for g in GREETINGS通用:
        patterns.append(g)
    return patterns


def generate_farewell_patterns():
    """Generate farewell patterns."""
    patterns = []
    for f in FAREWELLS:
        patterns.append(f)
        for prefix in SYSTEM_PHRASES:
            if prefix:
                patterns.append(f"{prefix} {f}")
    return patterns


def generate_thanks_patterns():
    """Generate thanks patterns."""
    patterns = []
    for t in THANKS:
        patterns.append(t)
    return patterns


def generate_chat_patterns():
    """Generate conversational patterns."""
    patterns = []
    for h in HOW_ARE_YOU:
        patterns.append(h)
    for i in IDENTITY:
        patterns.append(i)
    for c in CAPABILITIES:
        patterns.append(c)
    for j in JOKES:
        patterns.append(j)
    for w in WEATHER:
        patterns.append(w)
    for t in TIME_PATTERNS:
        patterns.append(t)
    for d in DATE_PATTERNS:
        patterns.append(d)
    return patterns


def generate_calc_patterns():
    """Generate calculator patterns."""
    patterns = []
    for prefix in CALC_PREFIXES:
        for expr in CALC_EXAMPLES:
            patterns.append(f"{prefix} {expr}")
    return patterns


def generate_file_patterns():
    """Generate file operation patterns."""
    patterns = []
    for action, variations in FILE_OPS:
        for v in variations:
            patterns.append(v)
            for prefix in SYSTEM_PHRASES:
                if prefix:
                    patterns.append(f"{prefix} {v}")
    return patterns


def generate_context_followups():
    """Generate context-aware follow-up patterns."""
    patterns = []
    followups = [
        "what about", "how about", "and", "also", "then", "after that",
        "can you also", "could you also", "please also", "and also",
        "one more thing", "oh and", "also open", "also close",
    ]
    for f in followups:
        for app in APPS[:20]:  # Top 20 apps
            patterns.append(f"{f} {app}")
    return patterns


def generate_iwant_patterns():
    """Generate 'I want to' / 'I need to' patterns."""
    patterns = []
    starters = ["i want to", "i need to", "i'd like to", "i wanna", "i gotta", "let me"]
    for starter in starters:
        for app in APPS[:20]:
            patterns.append(f"{starter} open {app}")
        for action in ["search", "google", "find"]:
            for topic in SEARCH_TOPICS[:15]:
                patterns.append(f"{starter} {action} {topic}")
    return patterns


def generate_can_patterns():
    """Generate 'Can you' patterns."""
    patterns = []
    starters = ["can you", "could you", "will you", "would you", "please"]
    for starter in starters:
        for app in APPS[:20]:
            patterns.append(f"{starter} open {app}")
            patterns.append(f"{starter} close {app}")
        for action in ["search", "google", "find"]:
            for topic in SEARCH_TOPICS[:15]:
                patterns.append(f"{starter} {action} {topic}")
        for sys_action in ["mute", "unmute", "screenshot", "lock", "shutdown", "restart"]:
            patterns.append(f"{starter} {sys_action}")
    return patterns


def generate_all_patterns():
    """Combine all pattern generators."""
    all_patterns = set()

    generators = [
        generate_app_patterns,
        generate_system_patterns,
        generate_web_patterns,
        generate_media_patterns,
        generate_nav_patterns,
        generate_chain_patterns,
        generate_greeting_patterns,
        generate_farewell_patterns,
        generate_thanks_patterns,
        generate_chat_patterns,
        generate_calc_patterns,
        generate_file_patterns,
        generate_context_followups,
        generate_iwant_patterns,
        generate_can_patterns,
    ]

    for gen in generators:
        patterns = gen()
        all_patterns.update(patterns)

    return sorted(all_patterns)


def generate_pattern_list_file():
    """Generate the patterns Python file."""
    patterns = generate_all_patterns()

    # Write as Python file
    with open("patterns_db.py", "w", encoding="utf-8") as f:
        f.write('"""\n')
        f.write('Auto-generated offline patterns for Laura NLP.\n')
        f.write(f'Total patterns: {len(patterns)}\n')
        f.write('Generated by generate_patterns.py\n')
        f.write('"""\n\n')
        f.write(f"PATTERNS_COUNT = {len(patterns)}\n\n")
        f.write("PATTERNS = [\n")
        for p in patterns:
            escaped = p.replace("\\", "\\\\").replace('"', '\\"')
            f.write(f'    "{escaped}",\n')
        f.write("]\n")

    # Also write as JSON for reference
    with open("patterns_db.json", "w", encoding="utf-8") as f:
        json.dump({"count": len(patterns), "patterns": patterns}, f, indent=2)

    print(f"Generated {len(patterns)} patterns")
    print(f"Written to: patterns_db.py and patterns_db.json")

    return patterns


if __name__ == "__main__":
    patterns = generate_pattern_list_file()

    # Print stats
    print(f"\n--- Stats ---")
    print(f"Total unique patterns: {len(patterns)}")
    print(f"App patterns: {len(generate_app_patterns())}")
    print(f"System patterns: {len(generate_system_patterns())}")
    print(f"Web patterns: {len(generate_web_patterns())}")
    print(f"Media patterns: {len(generate_media_patterns())}")
    print(f"Nav patterns: {len(generate_nav_patterns())}")
    print(f"Chain patterns: {len(generate_chain_patterns())}")
    print(f"Greeting patterns: {len(generate_greeting_patterns())}")
    print(f"Chat patterns: {len(generate_chat_patterns())}")
    print(f"File patterns: {len(generate_file_patterns())}")
    print(f"Context followups: {len(generate_context_followups())}")
    print(f"'I want' patterns: {len(generate_iwant_patterns())}")
    print(f"'Can you' patterns: {len(generate_can_patterns())}")
