import sys
import os
import json
import socket
import ssl
import threading
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Reload config after env vars are set
import config
import importlib
importlib.reload(config)

from processor import Processor
from executor import Executor
from speaker import Speaker
from memory import log_conversation
from scheduler import get_account_list, set_selected_accounts, get_bot_status, start_bot_for_account, stop_bot_for_account, load_accounts

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

processor = Processor()
executor = Executor()
speaker = Speaker()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Pine Bridge Remote</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 28px;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #888; font-size: 14px; margin-top: 5px; }
        .status {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 10px 20px;
            margin-bottom: 20px;
            font-size: 13px;
        }
        .status.connected { border: 1px solid #00ff88; color: #00ff88; }
        .status.disconnected { border: 1px solid #ff4444; color: #ff4444; }
        .mic-btn {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(145deg, #3a7bd5, #00d2ff);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            transition: all 0.3s;
            box-shadow: 0 10px 40px rgba(0, 210, 255, 0.3);
        }
        .mic-btn:active, .mic-btn.active {
            transform: scale(1.1);
            box-shadow: 0 0 60px rgba(0, 210, 255, 0.8);
            background: linear-gradient(145deg, #ff6b6b, #ff8e53);
        }
        .mic-btn svg { width: 60px; height: 60px; fill: white; }
        .mic-label {
            font-size: 14px;
            color: #888;
            margin-bottom: 10px;
        }
        .commands {
            width: 100%;
            max-width: 400px;
            margin-top: 20px;
        }
        .cmd-input {
            width: 100%;
            padding: 15px 20px;
            border-radius: 25px;
            border: 2px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 16px;
            outline: none;
        }
        .cmd-input::placeholder { color: #666; }
        .cmd-input:focus { border-color: #00d2ff; }
        .send-btn {
            width: 100%;
            padding: 15px;
            border-radius: 25px;
            border: none;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        .log {
            width: 100%;
            max-width: 400px;
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
        }
        .log-entry {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 13px;
        }
        .log-entry.user { color: #00d2ff; }
        .log-entry.assistant { color: #00ff88; }
        .log-entry.error { color: #ff4444; }
        .log-entry .time { color: #666; font-size: 11px; }
        .quick-cmds {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 15px;
            width: 100%;
            max-width: 400px;
        }
        .quick-cmd {
            padding: 8px 15px;
            border-radius: 20px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            font-size: 12px;
            cursor: pointer;
        }
        .quick-cmd:active { background: rgba(0, 210, 255, 0.3); }
        .work-mode {
            background: linear-gradient(145deg, #3a7bd5, #00d2ff) !important;
            border: none !important;
            font-weight: bold;
            font-size: 14px;
            padding: 12px 25px;
        }
        .work-mode:active { transform: scale(0.95); }
        .section-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 20px;
            margin-bottom: 10px;
            width: 100%;
            max-width: 400px;
        }
        .media-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            width: 100%;
            max-width: 400px;
            margin-bottom: 5px;
        }
        .media-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .media-btn:active { background: rgba(0, 210, 255, 0.4); transform: scale(0.95); }
        .media-btn svg { width: 28px; height: 28px; fill: white; }
        .media-btn.play-btn {
            width: 70px;
            height: 70px;
            background: linear-gradient(145deg, #3a7bd5, #00d2ff);
            border: none;
        }
        .media-btn.play-btn:active { transform: scale(0.9); }
        .media-btn.small { width: 50px; height: 50px; }
        .media-btn.small svg { width: 24px; height: 24px; }
        /* Joystick */
        .nav-section {
            width: 100%;
            max-width: 400px;
            margin-top: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 14px;
        }
        .joystick-row {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .joystick-wrap {
            position: relative;
            width: 160px;
            height: 160px;
            border-radius: 50%;
            background: rgba(255,255,255,0.06);
            border: 2px solid rgba(255,255,255,0.15);
            touch-action: none;
            -webkit-user-select: none;
            user-select: none;
        }
        .joystick-knob {
            position: absolute;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(145deg, #3a7bd5, #00d2ff);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 4px 20px rgba(0,210,255,0.4);
            pointer-events: none;
            transition: box-shadow 0.15s;
        }
        .joystick-wrap.active .joystick-knob {
            box-shadow: 0 4px 30px rgba(0,210,255,0.7);
        }
        .joystick-clicks {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .nav-btn {
            width: 60px;
            height: 44px;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .nav-btn:active { background: rgba(0,210,255,0.4); transform: scale(0.93); }
        .nav-btn svg { width: 20px; height: 20px; fill: white; }
        .scroll-row {
            display: flex;
            gap: 10px;
        }
        .bot-section {
            width: 100%;
            max-width: 400px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .bot-accounts {
            margin-bottom: 15px;
        }
        .account-chip {
            padding: 6px 12px;
            border-radius: 15px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .account-chip.selected {
            background: linear-gradient(145deg, #3a7bd5, #00d2ff);
            border-color: #00d2ff;
        }
        .account-chip:active { transform: scale(0.95); }
        .status-btn {
            width: 100%;
            padding: 12px;
            border-radius: 20px;
            border: 2px solid rgba(0,255,136,0.4);
            background: rgba(0,255,136,0.1);
            color: #00ff88;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .status-btn:active { background: rgba(0,255,136,0.3); transform: scale(0.97); }
        .bot-status-wrap { margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Pine Bridge</h1>
        <p>Remote Control</p>
    </div>
    
    <div class="status" id="status">Connecting...</div>
    
    <p class="mic-label">Hold to speak</p>
    <button class="mic-btn" id="micBtn">
        <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
    </button>
    
    <div class="section-label">Media Controls</div>
    <div class="media-controls">
        <button class="media-btn" onclick="sendCmd('previous track')">
            <svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
        </button>
        <button class="media-btn play-btn" onclick="sendCmd('pause')">
            <svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <button class="media-btn" onclick="sendCmd('next track')">
            <svg viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
        </button>
    </div>
    <div class="media-controls">
        <button class="media-btn small" onclick="sendCmd('volume down')">
            <svg viewBox="0 0 24 24"><path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/></svg>
        </button>
        <button class="media-btn small" id="muteBtn" onclick="toggleMute()">
            <svg id="muteIcon" viewBox="0 0 24 24"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
            <svg id="unmuteIcon" style="display:none" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
        </button>
        <button class="media-btn small" onclick="sendCmd('volume up')">
            <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
        </button>
    </div>
    
    <div class="section-label">Navigation</div>
    <div class="nav-section">
        <div class="joystick-row">
            <div class="joystick-clicks">
                <div class="nav-btn" onclick="sendCmd('scroll up')">
                    <svg viewBox="0 0 24 24"><path d="M7 14l5-5 5 5z"/></svg>
                </div>
                <div class="nav-btn" onclick="sendCmd('left click')">L-Click</div>
                <div class="nav-btn" onclick="sendCmd('right click')">R-Click</div>
            </div>
            <div class="joystick-wrap" id="joystick">
                <div class="joystick-knob" id="joystickKnob"></div>
            </div>
            <div class="joystick-clicks">
                <div class="nav-btn" onclick="sendCmd('scroll down')">
                    <svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
                </div>
                <div class="nav-btn" onclick="sendCmd('double click')">D-Click</div>
                <div class="nav-btn" onclick="sendCmd('press enter')">Enter</div>
            </div>
        </div>
    </div>
    
    <div class="section-label">Quick Commands</div>
    <div class="quick-cmds">
        <div class="quick-cmd" onclick="sendCmd('what time is it')">Time</div>
        <div class="quick-cmd" onclick="sendCmd('what is the date')">Date</div>
        <div class="quick-cmd" onclick="sendCmd('screenshot')">Screenshot</div>
        <div class="quick-cmd" onclick="sendCmd('open chrome')">Chrome</div>
        <div class="quick-cmd" onclick="sendCmd('open spotify')">Spotify</div>
        <div class="quick-cmd" onclick="sendCmd('open youtube')">YouTube</div>
        <div class="quick-cmd" onclick="sendCmd('shutdown')">Shutdown</div>
        <div class="quick-cmd" onclick="sendCmd('lock')">Lock</div>
    </div>
    
    <div class="section-label">Modes</div>
    <div class="quick-cmds">
        <div class="quick-cmd work-mode" onclick="workMode()">Work Mode</div>
    </div>
    
    <div class="section-label">Trading Bot</div>
    <div class="bot-section">
        <div class="bot-accounts" id="botAccounts">
            <p style="color:#888; font-size:12px; margin-bottom:10px;">Select accounts to run:</p>
            <div id="accountList" style="display:flex; flex-wrap:wrap; gap:6px;"></div>
            <button class="send-btn" style="margin-top:10px; font-size:13px; padding:10px;" onclick="startSelectedBots()">Start Selected</button>
            <button class="send-btn" style="margin-top:6px; font-size:13px; padding:10px; background: linear-gradient(90deg, #ff4444, #ff6b6b);" onclick="stopAllBots()">Stop All Bots</button>
        </div>
        <div class="bot-status-wrap">
            <button class="status-btn" id="botStatusBtn" onclick="checkBotStatus()">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                Bot Status
            </button>
            <div id="botStatusResult" style="margin-top:10px; font-size:12px; color:#888;"></div>
        </div>
    </div>
    
    <div class="commands">
        <input type="text" class="cmd-input" id="cmdInput" placeholder="Type a command..." 
               onkeypress="if(event.key==='Enter')sendTextCmd()">
        <button class="send-btn" onclick="sendTextCmd()">Send Command</button>
    </div>
    
    <div class="log" id="log"></div>

    <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        const micBtn = document.getElementById('micBtn');
        const cmdInput = document.getElementById('cmdInput');
        const logDiv = document.getElementById('log');
        const statusDiv = document.getElementById('status');
        let mediaRecorder = null;
        let audioChunks = [];

        socket.on('connect', () => {
            statusDiv.textContent = 'Connected to laptop';
            statusDiv.className = 'status connected';
            addLog('Connected to Pine Bridge', 'assistant');
        });

        socket.on('disconnect', () => {
            statusDiv.textContent = 'Disconnected';
            statusDiv.className = 'status disconnected';
        });

        socket.on('response', (data) => {
            addLog(data.message, data.success ? 'assistant' : 'error');
        });

        function addLog(text, type) {
            const time = new Date().toLocaleTimeString();
            logDiv.innerHTML = `<div class="log-entry ${type}"><span class="time">${time}</span> ${text}</div>` + logDiv.innerHTML;
        }

        function sendCmd(cmd) {
            addLog(cmd, 'user');
            socket.emit('command', {command: cmd});
        }

        function sendTextCmd() {
            const cmd = cmdInput.value.trim();
            if (cmd) {
                sendCmd(cmd);
                cmdInput.value = '';
            }
        }

        function workMode() {
            addLog('Work Mode activated', 'user');
            socket.emit('command', {command: 'close all'});
            setTimeout(() => {
                socket.emit('command', {command: 'work mode greeting'});
            }, 1500);
            setTimeout(() => {
                socket.emit('command', {command: 'what time is it'});
            }, 3000);
            setTimeout(() => {
                socket.emit('command', {command: 'open tradingview'});
            }, 5000);
            setTimeout(() => {
                socket.emit('command', {command: 'open discord'});
            }, 6000);
            setTimeout(() => {
                socket.emit('command', {command: 'open unigram'});
            }, 7000);
            setTimeout(() => {
                socket.emit('command', {command: 'work mode music'});
            }, 8000);
        }

        let isMuted = false;
        function toggleMute() {
            isMuted = !isMuted;
            sendCmd(isMuted ? 'mute' : 'unmute');
            document.getElementById('muteIcon').style.display = isMuted ? 'none' : 'block';
            document.getElementById('unmuteIcon').style.display = isMuted ? 'block' : 'none';
        }

        // Voice recording
        micBtn.addEventListener('mousedown', startRecording);
        micBtn.addEventListener('mouseup', stopRecording);
        micBtn.addEventListener('mouseleave', stopRecording);
        micBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); });
        micBtn.addEventListener('touchend', (e) => { e.preventDefault(); stopRecording(); });

        // Joystick
        const joystick = document.getElementById('joystick');
        const joystickKnob = document.getElementById('joystickKnob');
        let joystickActive = false;
        let joystickCenter = {x: 0, y: 0};
        const JOYSTICK_RADIUS = 80;
        const KNOB_RADIUS = 28;
        const DEAD_ZONE = 10;
        const MOVE_SCALE = 0.3;

        function joystickStart(cx, cy) {
            const rect = joystick.getBoundingClientRect();
            joystickCenter = {x: rect.left + rect.width/2, y: rect.top + rect.height/2};
            joystickActive = true;
            joystick.classList.add('active');
            joystickMove(cx, cy);
        }

        function joystickMove(cx, cy) {
            if (!joystickActive) return;
            let dx = cx - joystickCenter.x;
            let dy = cy - joystickCenter.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            const maxDist = JOYSTICK_RADIUS - KNOB_RADIUS;
            if (dist > maxDist) {
                dx = dx / dist * maxDist;
                dy = dy / dist * maxDist;
            }
            joystickKnob.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
            if (dist > DEAD_ZONE) {
                const moveX = Math.round(dx * MOVE_SCALE);
                const moveY = Math.round(dy * MOVE_SCALE);
                socket.emit('mouse', {dx: moveX, dy: moveY});
            }
        }

        function joystickEnd() {
            joystickActive = false;
            joystick.classList.remove('active');
            joystickKnob.style.transform = 'translate(-50%, -50%)';
        }

        joystick.addEventListener('mousedown', (e) => { e.preventDefault(); joystickStart(e.clientX, e.clientY); });
        document.addEventListener('mousemove', (e) => { if (joystickActive) joystickMove(e.clientX, e.clientY); });
        document.addEventListener('mouseup', () => { if (joystickActive) joystickEnd(); });
        joystick.addEventListener('touchstart', (e) => { e.preventDefault(); const t = e.touches[0]; joystickStart(t.clientX, t.clientY); }, {passive: false});
        joystick.addEventListener('touchmove', (e) => { e.preventDefault(); const t = e.touches[0]; joystickMove(t.clientX, t.clientY); }, {passive: false});
        joystick.addEventListener('touchend', (e) => { e.preventDefault(); joystickEnd(); }, {passive: false});

        async function startRecording() {
            micBtn.classList.add('active');
            try {
                const stream = await navigator.mediaDevices.getUserMedia({audio: true});
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
                mediaRecorder.start();
            } catch (err) {
                addLog('Mic access denied', 'error');
            }
        }

        function stopRecording() {
            micBtn.classList.remove('active');
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                mediaRecorder.onstop = () => {
                    const blob = new Blob(audioChunks, {type: 'audio/webm'});
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        socket.emit('voice', {audio: reader.result});
                    };
                    reader.readAsDataURL(blob);
                };
            }
        }

        // Bot account selection
        let selectedAccounts = [];
        function loadAccounts() {
            socket.emit('get_accounts');
        }
        socket.on('accounts_list', (data) => {
            const list = document.getElementById('accountList');
            list.innerHTML = '';
            selectedAccounts = [];
            (data.accounts || []).forEach(name => {
                const chip = document.createElement('div');
                chip.className = 'account-chip';
                chip.textContent = name;
                chip.onclick = () => {
                    chip.classList.toggle('selected');
                    if (chip.classList.contains('selected')) {
                        selectedAccounts.push(name);
                    } else {
                        selectedAccounts = selectedAccounts.filter(a => a !== name);
                    }
                };
                list.appendChild(chip);
            });
        });
        function startSelectedBots() {
            if (selectedAccounts.length === 0) {
                addLog('Select at least one account', 'error');
                return;
            }
            socket.emit('start_bots', {accounts: selectedAccounts});
            addLog('Starting bots: ' + selectedAccounts.join(', '), 'user');
        }
        function stopAllBots() {
            socket.emit('stop_all_bots');
            addLog('Stopping all bots...', 'user');
        }
        function checkBotStatus() {
            socket.emit('get_bot_status');
            document.getElementById('botStatusResult').textContent = 'Checking...';
        }
        socket.on('bot_status', (data) => {
            const el = document.getElementById('botStatusResult');
            const status = data.status || {};
            const keys = Object.keys(status);
            if (keys.length === 0) {
                el.innerHTML = '<span style="color:#888">No bots running</span>';
            } else {
                el.innerHTML = keys.map(k => {
                    const s = status[k];
                    const color = s.running ? '#00ff88' : '#ff4444';
                    const label = s.running ? 'RUNNING' : 'STOPPED';
                    return '<span style="color:'+color+'; margin-right:10px;">'+k+': '+label+'</span>';
                }).join('');
            }
        });
        loadAccounts();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    print(f"\033[92m[WiFi]\033[0m Phone connected")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"\033[93m[WiFi]\033[0m Phone disconnected")

_debounce_timers = {}
_DEBOUNCE_CMDS = {"volume up", "volume down", "mute", "unmute", "next track", "previous track", "pause", "play"}
_SILENT_CMDS = {
    "mouse up", "mouse down", "mouse left", "mouse right",
    "click", "left click", "right click", "double click",
    "scroll up", "scroll down",
    "press up", "press down", "press left", "press right",
    "press enter", "press escape", "press tab", "press space",
    "press backspace", "press delete", "press home", "press end",
    "page up", "page down",
}
_DEBOUNCE_DELAY = 0.4  # seconds
_debounce_pending = []

@socketio.on('command')
def handle_command(data):
    command = data.get('command', '').lower().strip()
    print(f"\033[90m[Phone Command]\033[0m {command}")

    # Debounce rapid-fire commands: execute all, but only speak the last one
    if command in _DEBOUNCE_CMDS:
        _debounce_pending.append(command)
        if command in _debounce_timers:
            _debounce_timers[command].cancel()
        timer = threading.Timer(_DEBOUNCE_DELAY, _flush_debounced, args=[command])
        _debounce_timers[command] = timer
        timer.start()
        return

    # Navigation commands execute silently - no voice feedback
    if command in _SILENT_CMDS:
        _execute_command(command, speak=False)
        return

    _execute_command(command, speak=True)

def _flush_debounced(last_command):
    # Execute all queued commands silently, then speak only the last result
    pending = list(_debounce_pending)
    _debounce_pending.clear()
    for cmd in pending[:-1]:
        _execute_command(cmd, speak=False)
    if pending:
        _execute_command(pending[-1], speak=True)

def _execute_command(command, speak=True):
    executor.set_emitters(
        lambda event, data: socketio.emit(event, data),
        lambda msg, block=False: speaker.say(msg, block=block),
    )
    result = processor.process(command)
    if result is None:
        if speak:
            msg = "I'm not sure how to do that."
            speaker.say(msg, block=False)
            socketio.emit('response', {'message': msg, 'success': False})
        log_conversation(command, "I'm not sure how to do that.", False)
        return

    module, action, params = result
    success, message = executor.execute((module, action, params))
    if speak:
        speaker.say(message, block=False)
    socketio.emit('response', {'message': message, 'success': success})
    log_conversation(command, message, success)

@socketio.on('mouse')
def handle_mouse(data):
    import ctypes as _ct
    dx = int(data.get('dx', 0))
    dy = int(data.get('dy', 0))
    if dx != 0 or dy != 0:
        _ct.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)

@socketio.on('voice')
def handle_voice(data):
    import base64
    import tempfile
    import speech_recognition as sr

    audio_data = data.get('audio', '')
    if not audio_data:
        return

    print(f"\033[90m[Phone Voice]\033[0m Processing voice...")

    try:
        # Strip data URL prefix: "data:audio/webm;base64,..."
        if ',' in audio_data:
            audio_data = audio_data.split(',', 1)[1]

        audio_bytes = base64.b64decode(audio_data)

        # Save webm to temp file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
            f.write(audio_bytes)
            webm_path = f.name

        # Convert webm to wav using ffmpeg directly
        wav_path = webm_path.replace('.webm', '.wav')
        try:
            import imageio_ffmpeg
            import subprocess
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            subprocess.run([
                ffmpeg, '-y', '-i', webm_path,
                '-ar', '16000', '-ac', '1', '-f', 'wav', wav_path
            ], capture_output=True, check=True)
        except Exception as e:
            print(f"\033[93m[Phone Voice]\033[0m ffmpeg convert failed: {e}")
            wav_path = webm_path

        # Transcribe with Google STT
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language='en-US')
        print(f"\033[90m[Phone Voice]\033[0m \"{text}\"")

        # Cleanup temp files
        for p in [webm_path, wav_path]:
            try:
                os.remove(p)
            except:
                pass

        # Process as command
        result = processor.process(text.lower().strip())
        if result is None:
            msg = "I'm not sure how to do that."
            speaker.say(msg, block=False)
            socketio.emit('response', {'message': msg, 'success': False})
            log_conversation(text, msg, False)
            return

        module, action, params = result
        success, message = executor.execute((module, action, params))
        speaker.say(message, block=False)
        socketio.emit('response', {'message': message, 'success': success})
        log_conversation(text, message, success)

    except sr.UnknownValueError:
        msg = "I didn't catch that. Could you repeat?"
        speaker.say(msg, block=False)
        socketio.emit('response', {'message': msg, 'success': False})
    except Exception as e:
        print(f"\033[91m[Phone Voice]\033[0m Error: {e}")
        msg = "Voice processing failed."
        speaker.say(msg, block=False)
        socketio.emit('response', {'message': msg, 'success': False})

@socketio.on('get_accounts')
def handle_get_accounts():
    accounts = get_account_list()
    socketio.emit('accounts_list', {'accounts': accounts})

@socketio.on('start_bots')
def handle_start_bots(data):
    accounts = data.get('accounts', [])
    if not accounts:
        return
    set_selected_accounts(accounts)
    results = {}
    for acct in accounts:
        ok = start_bot_for_account(acct)
        results[acct] = "started" if ok else "failed"
    msg = "Bots started: " + ", ".join(f"{k} ({v})" for k, v in results.items())
    socketio.emit('response', {'message': msg, 'success': True})
    speaker.say(msg, block=False)

@socketio.on('stop_all_bots')
def handle_stop_all_bots():
    from scheduler import stop_all_bots
    stopped = stop_all_bots()
    if stopped:
        msg = f"Stopped bots: {', '.join(stopped)}"
    else:
        msg = "No bots were running."
    socketio.emit('response', {'message': msg, 'success': True})
    speaker.say(msg, block=False)

@socketio.on('get_bot_status')
def handle_get_bot_status():
    status = get_bot_status()
    socketio.emit('bot_status', {'status': status})

def run_server(host='0.0.0.0', port=5000):
    ip = get_local_ip()
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")

    use_ssl = os.path.exists(cert_path) and os.path.exists(key_path)
    scheme = "https" if use_ssl else "http"

    print(f"\n{'='*56}")
    print(f"  Pine Bridge WiFi Server")
    print(f"{'='*56}")
    print(f"  Phone URL:  {scheme}://{ip}:{port}")
    print(f"  Local URL:  {scheme}://127.0.0.1:{port}")
    print(f"{'='*56}\n")

    if use_ssl:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert_path, key_path)
        socketio.run(app, host=host, port=port, debug=False,
                     ssl_context=ctx, allow_unsafe_werkzeug=True)
    else:
        socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    run_server()
