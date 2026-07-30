# voice/microphone_io.py

from config import (
    SAMPLE_RATE,
    MIC_INPUT_FILE,
    WHISPER_MODEL_SIZE,
    CHUNK_DURATION,
    SILENCE_THRESHOLD,
    SILENCE_SECONDS_TO_STOP,
    MAX_RECORD_SECONDS,
    MIN_RECORD_SECONDS,
)


CHANNELS = 1
stt_model = None


def get_sounddevice():
    try:
        import sounddevice as sd
    except ImportError as e:
        raise RuntimeError("sounddevice is not installed. Run: python -m pip install sounddevice") from e

    return sd


def get_stt_model():
    global stt_model

    if stt_model is not None:
        return stt_model

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "faster-whisper is not installed. Run: python -m pip install faster-whisper"
        ) from e

    print("Loading speech-to-text model...")
    stt_model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device="cpu",
        compute_type="int8",
    )
    print("Speech-to-text model ready.")

    return stt_model


def show_microphones():
    sd = get_sounddevice()

    print()
    print("Available audio devices:")
    print(sd.query_devices())
    print()


def calculate_volume(audio_chunk):
    import numpy as np

    return float(np.sqrt(np.mean(audio_chunk ** 2)))


def record_until_silence():
    import numpy as np
    import soundfile as sf

    sd = get_sounddevice()

    print()
    print("Listening...")
    print("Start speaking. I will stop recording when you are silent.")

    chunk_samples = int(CHUNK_DURATION * SAMPLE_RATE)

    recorded_chunks = []

    started_speaking = False
    silence_duration = 0.0
    total_duration = 0.0

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
    ) as stream:

        while True:
            audio_chunk, overflowed = stream.read(chunk_samples)

            if overflowed:
                print("Audio buffer overflow warning.")

            recorded_chunks.append(audio_chunk.copy())

            volume = calculate_volume(audio_chunk)
            total_duration += CHUNK_DURATION

            if volume > SILENCE_THRESHOLD:
                started_speaking = True
                silence_duration = 0.0
                print(f"Speaking... volume={volume:.4f}", end="\r")
            else:
                if started_speaking:
                    silence_duration += CHUNK_DURATION
                    print(f"Silence... {silence_duration:.1f}s", end="\r")
                else:
                    print(f"Waiting for speech... volume={volume:.4f}", end="\r")

            if (
                started_speaking
                and total_duration >= MIN_RECORD_SECONDS
                and silence_duration >= SILENCE_SECONDS_TO_STOP
            ):
                print()
                print("Detected silence. Stopping recording.")
                break

            if total_duration >= MAX_RECORD_SECONDS:
                print()
                print("Maximum recording time reached. Stopping recording.")
                break

    audio = np.concatenate(recorded_chunks, axis=0)

    sf.write(
        MIC_INPUT_FILE,
        audio,
        SAMPLE_RATE,
    )

    return MIC_INPUT_FILE


def transcribe_audio(file_path):
    segments, info = get_stt_model().transcribe(
        file_path,
        beam_size=5,
        language="en",
    )

    text_parts = []

    for segment in segments:
        text_parts.append(segment.text.strip())

    return " ".join(text_parts).strip()


def listen_to_user():
    audio_file = record_until_silence()
    text = transcribe_audio(audio_file)

    print()
    print("Visitor said:")
    print(text if text else "[No speech detected]")

    return text
