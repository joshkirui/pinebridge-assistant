@echo off
REM Pine Bridge Auto-Start
cd /d C:\Users\joshk\pine-bridge
set DEEPSEEK_API_KEY=sk-9b69f66d696046b5863b7dee38454702
set ELEVENLABS_API_KEY=sk_e81bd71c7d60578f3a7dc9d2dcdc0a2661a0b99dad4d2401
set PINEBRIDGE_TTS=elevenlabs
set ELEVENLABS_VOICE_ID=FGY2WhTYpPnrIDTdsKH5
py -3.11 wifi_server.py
