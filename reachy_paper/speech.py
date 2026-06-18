# speech.py

import pyttsx3


def say_message(message, rate=155, volume=1.0):
    """
    Read message using text-to-speech.
    """

    engine = pyttsx3.init()

    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    print("Reachy says:")
    print(message)

    engine.say(message)
    engine.runAndWait()