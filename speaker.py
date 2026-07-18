import sys
import io
import threading
import tempfile
import os
import queue
from config import ASSISTANT_NAME

DEFAULT_ELEVENLABS_VOICE = "21m00Tcm4TlvDq8ikWAM"


class Speaker:
    def __init__(self):
        self._backend = os.environ.get("PINEBRIDGE_TTS", "elevenlabs")
        self._elevenlabs_client = None
        self._pyttsx_engine = None
        self._pygame_inited = False
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._tts_thread = None

        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
        elevenlabs_voice = os.environ.get("ELEVENLABS_VOICE_ID", "FGY2WhTYpPnrIDTdsKH5")

        if self._backend == "elevenlabs" and elevenlabs_key:
            try:
                from elevenlabs.client import ElevenLabs
                client = ElevenLabs(api_key=elevenlabs_key)
                client.voices.get_all()
                self._elevenlabs_client = client
                self._elevenlabs_voice_id = elevenlabs_voice
                self._backend = "elevenlabs"
                self._init_pygame()
                print(f"\033[92m[TTS]\033[0m ElevenLabs connected (Laura voice)")
            except Exception as e:
                print(f"\033[93m[TTS]\033[0m ElevenLabs error: {e}, using pyttsx3")
                self._backend = "pyttsx3"
        else:
            print(f"\033[93m[TTS]\033[0m No ElevenLabs key, using pyttsx3")
            self._backend = "pyttsx3"

        if self._backend == "pyttsx3" or self._elevenlabs_client is None:
            self._init_pyttsx()

        self._start_tts_worker()

    def _init_pygame(self):
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self._pygame_inited = True
        except Exception as e:
            print(f"\033[93m[Speaker]\033[0m pygame init failed: {e}")

    def _init_pyttsx(self):
        try:
            import pyttsx3
            self._pyttsx_engine = pyttsx3.init()
            self._pyttsx_engine.setProperty("rate", TTS_RATE)
            self._pyttsx_engine.setProperty("volume", TTS_VOLUME)
            voices = self._pyttsx_engine.getProperty("voices")
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower() or "hazel" in v.name.lower():
                    self._pyttsx_engine.setProperty("voice", v.id)
                    break
            self._backend = "pyttsx3"
        except Exception as e:
            print(f"\033[91m[Speaker]\033[0m pyttsx3 init failed: {e}")
            self._backend = "print_only"

    def _start_tts_worker(self):
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()

    def _tts_worker(self):
        while True:
            try:
                text = self._queue.get()
                if text is None:
                    break
                self._speak_now(text)
                self._queue.task_done()
            except Exception:
                pass

    def say(self, text, block=True):
        print(f"\033[96m[{ASSISTANT_NAME}]\033[0m {text}")

        if block:
            self._speak_now(text)
        else:
            self._queue.put(text)

    def _speak_now(self, text):
        try:
            if self._backend == "elevenlabs" and self._elevenlabs_client:
                self._speak_elevenlabs(text)
            elif self._backend == "pyttsx3" and self._pyttsx_engine:
                self._speak_pyttsx(text)
        except Exception as e:
            print(f"\033[91m[Speaker]\033[0m TTS error: {e}")

    def _speak_elevenlabs(self, text):
        try:
            audio_iterator = self._elevenlabs_client.text_to_speech.convert(
                voice_id=self._elevenlabs_voice_id,
                model_id="eleven_turbo_v2_5",
                text=text,
            )
            audio_bytes = b"".join(audio_iterator)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            try:
                if self._pygame_inited:
                    import pygame
                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(50)
                else:
                    from elevenlabs import play
                    play(audio_bytes)
            finally:
                try:
                    os.remove(temp_path)
                except:
                    pass
        except Exception as e:
            print(f"\033[93m[TTS]\033[0m ElevenLabs error: {e}")
            if self._pyttsx_engine:
                self._speak_pyttsx(text)

    def _speak_pyttsx(self, text):
        if self._pyttsx_engine:
            with self._lock:
                try:
                    self._pyttsx_engine.say(text)
                    self._pyttsx_engine.runAndWait()
                except RuntimeError:
                    pass

    def listen_feedback(self):
        self.say("I'm listening...")

    def not_heard(self):
        self.say("I didn't catch that. Could you repeat?")

    def command_received(self, command):
        self.say(f"Got it. {command}")

    def error(self, msg="Something went wrong."):
        self.say(msg)

    def ready(self):
        mode = f" [AI: {self._backend}]"
        self.say(f"Hi Lerito, let's cook! {mode}")

    def shutting_down(self):
        self.say("Shutting down. Goodbye!")
        if self._pygame_inited:
            try:
                import pygame
                pygame.mixer.quit()
            except:
                pass

    def no_ai(self):
        self.say("No AI API key set. Using offline mode only.")
