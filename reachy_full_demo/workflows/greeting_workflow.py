from voice.speech_io import say
from robot.motion import look_forward, greeting_hand


def run_greeting(reachy):
    look_forward(reachy)
    greeting_hand(reachy)

    say(
        "Hello everyone. I am Reachy, your Deakin campus guide. "
        "I can greet visitors, hand over an object, and answer questions about Deakin."
    )

    say("First, I will demonstrate my grasping movement.")