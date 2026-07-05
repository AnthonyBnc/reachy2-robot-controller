# microphone_io.py

import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

from config import (
    RECORD_SECONDS,
    SAMPLE_RATE,
    MIC_INPUT_FILE,
    WHISPER_MODEL_SIZE,
)


print("Loading speech-to-text model...")
stt_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device="cpu",
    compute_type="int8",
)
print("Speech-to-text model ready.")


def show_microphones():
    print()
    print("Available audio devices:")
    print(sd.query_devices())
    print()


def record_question():
    """
    Record visitor voice from laptop microphone.
    """

    print()
    print(f"Recording for {RECORD_SECONDS} seconds...")
    print("Please speak now.")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )

    sd.wait()

    sf.write(
        MIC_INPUT_FILE,
        audio,
        SAMPLE_RATE,
    )

    print("Recording finished.")
    return MIC_INPUT_FILE


def transcribe_audio(file_path):
    """
    Convert recorded audio to text.
    """

    segments, info = stt_model.transcribe(
        file_path,
        beam_size=5,
        language="en",
    )

    text_parts = []

    for segment in segments:
        text_parts.append(segment.text.strip())

    text = " ".join(text_parts).strip()

    return text


def listen_to_user():
    """
    Record and transcribe user speech.
    """

    audio_file = record_question()
    text = transcribe_audio(audio_file)

    print()
    print("Visitor said:")
    print(text if text else "[No speech detected]")

    return text