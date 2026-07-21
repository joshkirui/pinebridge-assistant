import speech_recognition as sr
import sys
import os
import time
import threading
import numpy as np
from config import WAKE_WORD, STT_LANGUAGE, MIC_MONITOR_ENABLED

WAKE_PHRASES = [
    "hey laura",
    "hi laura",
    "hey lara",
    "hi lara",
    "hey laura",
    "hey pine bridge",
    "hey pinebrigde",
    "hey pine brige",
    "hey pain bridge",
    "hey bain bridge",
    "hey bainbridge",
    "hey painbridge",
    "hey pine brid",
    "hey pine br",
    "hey la",
    "hey lor",
    "hey ler",
    "hey lau",
    "hey lau ra",
    "hey lora",
    "hey lorah",
    "hey lahura",
    "hey lahrah",
]

FOLLOW_UP_TIMEOUT = 5.0
FOLLOW_UP_PHRASE_LIMIT = 8


class AudioMuter:
    def __init__(self):
        self._was_muted = False
        self._volume = None
        self._init()

    def _init(self):
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume = interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            self._volume = None

    def mute_all(self):
        if self._volume:
            try:
                self._was_muted = self._volume.GetMute()
                if not self._was_muted:
                    self._volume.SetMute(1, None)
                return True
            except Exception:
                pass
        return False

    def unmute_all(self):
        if self._volume:
            try:
                if not self._was_muted:
                    self._volume.SetMute(0, None)
                return True
            except Exception:
                pass
        return False

    def is_available(self):
        return self._volume is not None


class MicMonitor:
    def __init__(self):
        self._active = False
        self._level = 0.0
        self._thread = None
        self._stop = False
        self._pyaudio = None
        self._stream = None

    def _init_pyaudio(self):
        try:
            import pyaudio
            self._pyaudio = pyaudio.PyAudio()
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
            )
            return True
        except Exception:
            return False

    def start(self):
        self._active = True
        self._stop = False
        if not self._init_pyaudio():
            return
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False
        self._stop = True
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
                pass

    def _monitor_loop(self):
        while not self._stop:
            if not self._active:
                time.sleep(0.1)
                continue
            try:
                data = self._stream.read(1024, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = np.sqrt(np.mean(samples ** 2))
                normalized = min(rms / 5000.0, 1.0)
                self._level = normalized
                self._draw_bar(normalized)
            except Exception:
                time.sleep(0.05)

    def _draw_bar(self, level):
        bar_len = 30
        filled = int(level * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        if level > 0.6:
            color = "\033[91m"
        elif level > 0.3:
            color = "\033[93m"
        elif level > 0.05:
            color = "\033[92m"
        else:
            color = "\033[90m"

        reset = "\033[0m"
        heartbeat = "♥" if level > 0.05 else "♡"
        sys.stdout.write(f"\r  {color}{heartbeat} MIC {bar}{reset} ")
        sys.stdout.flush()

    def clear_line(self):
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()


class Listener:
    def __init__(self, speaker):
        self.speaker = speaker
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.05
        self.recognizer.dynamic_energy_ratio = 1.2
        self.recognizer.pause_threshold = 0.3
        self.recognizer.phrase_threshold = 0.1
        self.recognizer.non_speaking_duration = 0.15
        self.microphone = sr.Microphone()
        self.monitor = MicMonitor()
        self.muter = AudioMuter()
        self._ptt_mode = False
        self._always_on = True
        self._follow_up_active = False
        self._calibrate()

    def _calibrate(self):
        print("\033[93m[Calibrating microphone...]\033[0m")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"\033[92m[Calibrated. Energy threshold: {self.recognizer.energy_threshold:.0f}]\033[0m")

    def _matches_wake(self, text):
        text = text.lower().strip()
        for phrase in WAKE_PHRASES:
            if phrase in text:
                return True
        words = text.split()
        if "hey" in words and "pine" in words and "bridge" in words:
            return True
        if "hey" in words and "pine" in words and any(w.startswith("br") for w in words):
            return True
        # Fuzzy match: "hey" + anything that starts with "l" (laura, lara, etc.)
        if "hey" in words or "hi" in words:
            for w in words:
                if w.startswith("l") and len(w) >= 2:
                    return True
        return False

    def _strip_wake_word(self, text):
        text = text.lower().strip()
        for phrase in WAKE_PHRASES:
            if phrase in text:
                text = text.replace(phrase, "").strip()
                break
        words = text.split()
        if len(words) >= 2 and words[0] in ("hey", "hi") and words[1] in ("laura", "pine", "pain", "bain"):
            text = " ".join(words[2:]).strip()
        return text if text else None

    def listen_for_wake_word(self):
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
            try:
                text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE).lower()
                if text.strip():
                    print(f"\r\033[90m[Heard]\033[0m {text}          ")
                if self._matches_wake(text):
                    return True
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"\r\033[91m[STT Error]\033[0m {e}")
                time.sleep(1)
        except Exception:
            pass
        return False

    def listen_always_on(self):
        print("\033[93m[Always-On Mode]\033[0m Listening for 'Hey Laura'...")
        self.monitor._active = True

        while True:
            try:
                # Mute background audio before listening for wake word
                self.muter.mute_all()

                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)

                try:
                    text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE).lower()
                    if text.strip():
                        print(f"\r\033[90m[Heard]\033[0m {text}          ")

                    if not self._matches_wake(text):
                        # Unmute if no wake word detected
                        self.muter.unmute_all()
                        continue

                    print("\n\033[92m[WAKE DETECTED]\033[0m Listening for command...")

                    with self.microphone as source:
                        cmd_audio = self.recognizer.listen(source, timeout=30, phrase_time_limit=30)

                    try:
                        command = self.recognizer.recognize_google(cmd_audio, language=STT_LANGUAGE)
                        print(f"\033[92m[Command]\033[0m {command}")
                        self.muter.unmute_all()
                        self.monitor.clear_line()
                        return command.lower().strip()

                    except sr.UnknownValueError:
                        print("\033[93m[Didn't catch that]\033[0m")
                        self.muter.unmute_all()
                        self.monitor.clear_line()
                    except sr.RequestError as e:
                        print(f"\033[91m[STT Error]\033[0m {e}")
                        self.muter.unmute_all()

                except sr.UnknownValueError:
                    self.muter.unmute_all()
                    pass
                except sr.RequestError as e:
                    print(f"\r\033[91m[STT Error]\033[0m {e}")
                    self.muter.unmute_all()
                    time.sleep(1)

            except Exception as e:
                print(f"\033[91m[Error]\033[0m {e}")
                self.muter.unmute_all()
                time.sleep(0.5)

    def _follow_up_window(self, context):
        print(f"\033[90m[Follow-up] Listening for {FOLLOW_UP_TIMEOUT}s...\033[0m")
        self._follow_up_active = True
        start = time.time()

        while time.time() - start < FOLLOW_UP_TIMEOUT:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=FOLLOW_UP_TIMEOUT - (time.time() - start), phrase_time_limit=FOLLOW_UP_PHRASE_LIMIT)

                try:
                    text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE).lower().strip()
                    if text:
                        print(f"\033[92m[Follow-up]\033[0m {text}")
                        self._follow_up_active = False
                        return text
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    break
            except sr.WaitTimeoutError:
                break
            except Exception:
                break

        self._follow_up_active = False
        print("\033[90m[Follow-up window closed]\033[0m")
        return None

    def listen_for_push_to_talk(self):
        import keyboard
        print("\033[93m[PTT Mode]\033[0m Hold Ctrl+Alt to speak...")
        while True:
            keyboard.wait("ctrl+alt")
            print("\n\033[92m[PTT ACTIVE]\033[0m Listening...")
            self.monitor._active = True
            self.muter.mute_all()

            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=15, phrase_time_limit=30)

            self.monitor._active = False
            self.monitor.clear_line()

            try:
                text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE)
                print(f"\033[92m[You said]\033[0m {text}")
                self.muter.unmute_all()
                return text.lower().strip()
            except sr.UnknownValueError:
                print("\033[93m[Didn't catch that]\033[0m")
                self.muter.unmute_all()
                return None
            except sr.RequestError as e:
                print(f"\033[91m[STT Error]\033[0m {e}")
                self.muter.unmute_all()
                self.speaker.error("Speech recognition unavailable.")
                return None

    def listen_for_command(self):
        self.monitor._active = True
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=20)
            self.monitor._active = False
            self.monitor.clear_line()
            text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE)
            return text.lower().strip()
        except sr.WaitTimeoutError:
            self.monitor._active = False
            return None
        except sr.UnknownValueError:
            self.monitor._active = False
            return None
        except sr.RequestError:
            self.monitor._active = False
            self.speaker.error("Speech recognition service is unavailable.")
            return None
        return None
