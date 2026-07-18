# Pine Bridge - Voice Assistant

A Siri-like voice assistant for Windows that responds to "Hey Pine Bridge".

## Features

- **Wake Word Detection**: Say "Hey Pine Bridge" to activate
- **Voice Commands**: Control your computer entirely by voice
- **App Management**: Open and close applications
- **System Control**: Shutdown, restart, lock, sleep, volume, brightness
- **Web Browsing**: Search Google, open websites, YouTube, Gmail
- **File Operations**: Create, open, delete files and folders
- **Media Control**: Play/pause, next/previous track
- **General Info**: Time, date, calculator, system info
- **AI Fallback**: Uses OpenAI for complex commands (optional)

## Supported Voice Commands

### Apps
- "Open Chrome" / "Launch Notepad" / "Start Spotify"
- "Close Chrome" / "Kill Firefox"

### System
- "Shutdown" / "Restart" / "Lock screen"
- "Volume up" / "Volume down" / "Set volume to 50"
- "Mute" / "Unmute"
- "Take a screenshot"
- "Sleep" / "Hibernate"

### Web
- "Search for Python tutorials"
- "Google machine learning"
- "Open YouTube for music"
- "Open Gmail"
- "Go to GitHub"

### Files
- "List files on desktop"
- "Create folder called Projects"
- "Open file notes.txt"
- "Delete old_file.txt"
- "Find document.pdf"

### Media
- "Next track" / "Previous song"
- "Play pause"

### General
- "What time is it?"
- "What's the date?"
- "Calculate 15 times 3"
- "What's 2 plus 2?"
- "Open Command Prompt"
- "Open File Explorer"

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set OpenAI API key for AI-powered commands:
```bash
set OPENAI_API_KEY=your-api-key-here
```

3. Run:
```bash
python main.py
```

## How It Works

1. **Listening Mode**: Assistant continuously listens for "Hey Pine Bridge"
2. **Wake Word Detected**: Listens for your command
3. **Processing**: Parses command using pattern matching or OpenAI
4. **Execution**: Executes the command and responds with voice + text
