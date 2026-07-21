# voice/speech_io.py

import os
import platform
import subprocess
import threading

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from config import (
    KOKORO_LANG_CODE,
    KOKORO_VOICE,
    OUTPUT_FILE,
    USE_SPEECH_OUTPUT,
)


print("Loading Kokoro TTS...")
kokoro_pipeline = KPipeline(lang_code=KOKORO_LANG_CODE)
print("Kokoro TTS ready.")


def _run_speech_motion(reachy, gesture):
    if reachy is None or gesture is None:
        return None, None

    try:
        from robot.motion import speaking_motion
    except Exception as e:
        print("Speech motion unavailable:", e)
        return None, None

    stop_event = threading.Event()
    motion_thread = threading.Thread(
        target=speaking_motion,
        args=(reachy, stop_event, gesture),
        daemon=True,
    )
    motion_thread.start()

    return stop_event, motion_thread


def play_audio(file_path):
    system = platform.system().lower()

    if "darwin" in system:
        subprocess.run(["afplay", file_path], check=False)

    elif "windows" in system:
        os.startfile(file_path)

    else:
        subprocess.run(["aplay", file_path], check=False)


def generate_voice(text):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    generator = kokoro_pipeline(
        text,
        voice=KOKORO_VOICE,
    )

    chunks = []

    for _, _, audio in generator:
        chunks.append(audio)

    if not chunks:
        raise RuntimeError("Kokoro did not generate audio.")

    full_audio = np.concatenate(chunks)

    sf.write(
        OUTPUT_FILE,
        full_audio,
        24000,
    )

    return OUTPUT_FILE


def say(text, reachy=None, gesture="calm"):
    print()
    print("Reachy says:")
    print(text)

    stop_event = None
    motion_thread = None

    if not USE_SPEECH_OUTPUT:
        stop_event, motion_thread = _run_speech_motion(reachy, gesture)

        if motion_thread is not None:
            preview_duration = min(4.0, max(1.0, len(text.split()) * 0.18))
            motion_thread.join(timeout=preview_duration)
            stop_event.set()
            motion_thread.join(timeout=1.5)

        return

    try:
        audio_file = generate_voice(text)
        stop_event, motion_thread = _run_speech_motion(reachy, gesture)
        play_audio(audio_file)

    except Exception as e:
        print("Speech error:", e)
        print("Text answer is shown above.")

    finally:
        if stop_event is not None:
            stop_event.set()

        if motion_thread is not None:
            motion_thread.join(timeout=1.5)
