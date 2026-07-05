# main.py

from ai_brain import (
    create_ai_client,
    ask_ai,
    create_conversation_history,
    add_user_message,
    add_assistant_message,
    trim_history,
)

from microphone_io import listen_to_user, show_microphones
from speech_io import say


EXIT_WORDS = [
    "quit",
    "exit",
    "stop",
    "goodbye",
    "bye",
]


def should_exit(text):
    lower_text = text.lower().strip()

    for word in EXIT_WORDS:
        if word in lower_text:
            return True

    return False


def main():
    print("Starting Reachy Deakin Voice Guide...")
    print("Press Enter to record a question.")
    print("Type 't' then Enter to type instead of speaking.")
    print("Type 'devices' to show microphone devices.")
    print("Type 'q' to quit.")
    print()

    try:
        client = create_ai_client()
        print("OpenRouter client ready.")
    except Exception as e:
        print("Failed to start OpenRouter client:", e)
        return

    conversation_history = create_conversation_history()

    intro = (
        "Hello, I am Reachy, your Deakin campus guide. "
        "You can ask me about courses, campus maps, buildings, or student services."
    )

    say(intro)
    add_assistant_message(conversation_history, intro)

    while True:
        command = input("\nPress Enter to speak, 't' to type, 'devices' for microphones, or 'q' to quit: ").strip()

        if command.lower() == "q":
            say("Goodbye. Have a great day at Deakin.")
            break

        if command.lower() == "devices":
            show_microphones()
            continue

        if command.lower() == "t":
            user_text = input("Visitor asks: ").strip()
        else:
            user_text = listen_to_user()

        if not user_text:
            say("Sorry, I could not hear that clearly. Could you please try again?")
            continue

        if should_exit(user_text):
            say("Goodbye. Have a great day at Deakin.")
            break

        try:
            add_user_message(conversation_history, user_text)
            conversation_history = trim_history(conversation_history)

            answer = ask_ai(
                client,
                conversation_history,
            )

            add_assistant_message(conversation_history, answer)

            say(answer)

        except Exception as e:
            print("Error:", e)
            say("Sorry, I had a problem answering that question. Please try again.")


if __name__ == "__main__":
    main()