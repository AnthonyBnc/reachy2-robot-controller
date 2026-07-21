# main.py

from ai.ai_brain import create_ai_client
from robot.connection import connect_reachy

from workflows.greeting_workflow import run_greeting
from workflows.grasp_workflow import run_grasp_demo
from workflows.conversation_workflow import run_conversation
from workflows.goodbye_workflow import run_goodbye


def run_one_demo_cycle(client, reachy, cycle_number):
    print()
    print("=" * 60)
    print(f"Starting demo cycle {cycle_number}")
    print("=" * 60)

    run_greeting(reachy)

    run_grasp_demo(
        reachy,
        label="first grasp demonstration",
    )

    run_conversation(
        client,
        reachy,
    )

    run_grasp_demo(
        reachy,
        label="conversation reward grasp",
    )

    run_goodbye(reachy)


def main():
    print("Starting continuous Reachy full demo.")
    print("Keep E-stop nearby.")
    print("Make sure the ball is in the recorded position before each grasp.")
    print()

    try:
        client = create_ai_client()
        print("OpenRouter client ready.")
    except Exception as e:
        print("Failed to start OpenRouter client:", e)
        return

    reachy = connect_reachy()

    cycle_number = 1

    while True:
        command = input("\nPress Enter to start next audience cycle, or type q to quit: ").strip()

        if command.lower() == "q":
            print("Demo stopped.")
            break

        run_one_demo_cycle(
            client,
            reachy,
            cycle_number,
        )

        cycle_number += 1

if __name__ == "__main__":
    main()
