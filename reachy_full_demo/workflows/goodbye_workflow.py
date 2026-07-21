# workflows/goodbye_workflow.py

from voice.speech_io import say


def run_goodbye(reachy=None):
    say(
        "Thank you for spending time with me. "
        "Goodbye, and have a great day at Deakin.",
        reachy,
        gesture="goodbye",
    )
