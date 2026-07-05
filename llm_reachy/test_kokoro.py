import numpy as np
import soundfile as sf
import subprocess
from kokoro import KPipeline

print("Loading Kokoro...")
pipeline = KPipeline(lang_code="a")

text = "Hello, I am Reachy. I am ready to help visitors at Deakin University."

print("Generating audio...")
generator = pipeline(
    text,
    voice="am_michael",
)

chunks = []

for _, _, audio in generator:
    chunks.append(audio)

if not chunks:
    raise RuntimeError("No audio generated.")

full_audio = np.concatenate(chunks)

output_file = "test_kokoro.wav"
sf.write(output_file, full_audio, 24000)

print(f"Saved audio to {output_file}")
print("Playing audio...")
subprocess.run(["afplay", output_file], check=False)

print("Done.")