# config.py

# =========================================================
# OpenRouter API
# =========================================================

OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"

OPENROUTER_MODEL = "openai/gpt-4o-mini"


# =========================================================
# Kokoro TTS
# =========================================================

# "a" = American English
# "b" = British English
KOKORO_LANG_CODE = "a"

# Senior male voice
KOKORO_VOICE = "am_adam"

OUTPUT_FILE = "reachy_response.wav"

USE_SPEECH_OUTPUT = True


# =========================================================
# Microphone recording
# =========================================================

RECORD_SECONDS = 6
SAMPLE_RATE = 16000
MIC_INPUT_FILE = "visitor_question.wav"

# faster-whisper model size
# Use "tiny" if it is slow
# Use "base" for better accuracy
WHISPER_MODEL_SIZE = "base"