import argparse
import platform

from voice.speech_io import say


def main():
    parser = argparse.ArgumentParser(description="Test Reachy speech through the computer speaker.")
    parser.add_argument(
        "--text",
        default="Hello, this is Reachy's speaker test.",
        help="Text to generate and play.",
    )
    args = parser.parse_args()

    print(f"Computer platform: {platform.system()}")
    print("Playing through the system default output device.")
    print("On Windows, select your external speaker in Settings > System > Sound > Output.")

    say(args.text, reachy=None, gesture=None)


if __name__ == "__main__":
    main()
