# workflows/conversation_workflow.py

from ai.ai_brain import (
    ask_ai,
    create_conversation_history,
    add_user_message,
    add_assistant_message,
    trim_history,
)

from voice.microphone_io import listen_to_user, show_microphones
from voice.speech_io import say
from robot.motion import nod

from config import MAX_QUESTIONS_PER_VISITOR


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


def run_conversation(client, reachy):
    conversation_history = create_conversation_history()

    say(
        "Now you can ask me a question about Deakin. "
        "For example, you can ask about courses, campus maps, buildings, or student services."
    )

    for question_number in range(MAX_QUESTIONS_PER_VISITOR):
        print()
        print(f"Conversation question {question_number + 1}/{MAX_QUESTIONS_PER_VISITOR}")

        command = input(
            "Press Enter to speak, type 't' to type, 'devices' for microphones, or 'skip' to finish: "
        ).strip()

        if command.lower() == "skip":
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
            say("No problem. I will finish this conversation section.")
            break

        try:
            nod(reachy)

            add_user_message(conversation_history, user_text)
            conversation_history = trim_history(conversation_history)

            answer = ask_ai(
                client,
                conversation_history,
            )

            add_assistant_message(conversation_history, answer)

            say(answer)

        except Exception as e:
            print("Conversation error:", e)
            say("Sorry, I had a problem answering that question. Please try again.")

    say("Thank you for chatting with me.")