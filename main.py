import sys
import signal
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ASSISTANT_NAME, AI_BACKEND, DEEPSEEK_API_KEY, OPENAI_API_KEY, ELEVENLABS_API_KEY
from speaker import Speaker
from listener import Listener
from processor import Processor
from executor import Executor


def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"\033[96m{'='*56}")
    print(f"  \033[1m{ASSISTANT_NAME}\033[0m\033[96m - Voice Assistant")
    print(f"{'='*56}")

    ai_status = "\033[92mON\033[0m" if (DEEPSEEK_API_KEY or OPENAI_API_KEY) else "\033[93mOFF (offline mode)\033[0m"
    tts_status = "\033[92mElevenLabs\033[0m" if ELEVENLABS_API_KEY else "\033[93mpyttsx3\033[0m"

    print(f"  AI Backend:     {ai_status}")
    print(f"  TTS Voice:      {tts_status}")
    print(f"  Mode:           \033[93mPush-to-Talk (Ctrl+Alt)\033[0m")
    print(f"  Mic Monitor:    \033[92mActive while speaking\033[0m")
    print(f"  Quit:           Ctrl+C")
    print(f"{'='*56}\n")


def main():
    speaker = Speaker()
    listener = Listener(speaker)
    processor = Processor()
    executor = Executor()

    def signal_handler(sig, frame):
        listener.monitor.stop()
        speaker.shutting_down()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print_banner()
    speaker.ready()

    while True:
        try:
            command = listener.listen_for_push_to_talk()

            if command is None:
                continue

            result = processor.process(command)

            if result is None:
                speaker.say("I'm not sure how to do that yet.")
                continue

            module, action, params = result
            print(f"\033[90m[Executing] {module}.{action}({params})\033[0m")
            success, message = executor.execute((module, action, params))

            if success:
                speaker.say(message)
            else:
                speaker.error(message)

        except KeyboardInterrupt:
            listener.monitor.stop()
            speaker.shutting_down()
            break
        except Exception as e:
            print(f"\033[91m[Error]\033[0m {e}")
            continue


if __name__ == "__main__":
    main()
