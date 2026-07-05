# speech_io.py

import os
import platform
import subprocess

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


def play_audio(file_path):
    system = platform.system().lower()

    if "darwin" in system:
        subprocess.run(["afplay", file_path], check=False)

    elif "windows" in system:
        os.startfile(file_path)

    else:
        subprocess.run(["aplay", file_path], check=False)


def generate_voice(text):
    """
    Generate Kokoro TTS audio.
    """

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


def say(text):
    """
    Speak answer through laptop or external speaker.
    """

    print()
    print("Reachy says:")
    print(text)

    if not USE_SPEECH_OUTPUT:
        return

    try:
        audio_file = generate_voice(text)
        play_audio(audio_file)

    except Exception as e:
        print("Speech error:", e)
        print("Text answer is shown above.")