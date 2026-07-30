# voice/speech_io.py

import os
import platform
import subprocess
import threading

if platform.system().lower() == "windows":
    import winsound
else:
    winsound = None

from config import (
    KOKORO_LANG_CODE,
    KOKORO_VOICE,
    OUTPUT_FILE,
    USE_SPEECH_OUTPUT,
)


kokoro_pipeline = None


def get_kokoro_pipeline():
    global kokoro_pipeline

    if kokoro_pipeline is not None:
        return kokoro_pipeline

    try:
        from kokoro import KPipeline
    except ImportError as e:
        raise RuntimeError("Kokoro TTS is not installed. Run: python -m pip install kokoro") from e

    print("Loading Kokoro TTS...")
    kokoro_pipeline = KPipeline(lang_code=KOKORO_LANG_CODE)
    print("Kokoro TTS ready.")

    return kokoro_pipeline


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

    if "windows" in system:
        winsound.PlaySound(file_path, winsound.SND_FILENAME)

    elif "darwin" in system:
        subprocess.run(["afplay", file_path], check=False)

    else:
        subprocess.run(["aplay", file_path], check=False)


def generate_voice(text):
    try:
        import numpy as np
        import soundfile as sf
    except ImportError as e:
        raise RuntimeError(
            "Speech dependencies are not installed. Run: python -m pip install numpy soundfile"
        ) from e

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    generator = get_kokoro_pipeline()(
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
