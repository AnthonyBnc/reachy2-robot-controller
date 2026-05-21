from reachy2_sdk import ReachySDK
import time

ROBOT_HOST = "YOUR_IP"  # change if Reachy's IP changes

def safe_call(label, func):
    try:
        result = func()
        print(f"[OK] {label}")
        if result is not None:
            print(result)
        return result
    except Exception as e:
        print(f"[FAILED] {label}")
        print("Error:", e)
        return None


def show_gripper_menu():
    print("""
=============================
 Reachy Hand Controller
=============================

Choose hand:
1 - Left hand
2 - Right hand
3 - Both hands
4 - Show hand status
5 - Show available hand functions
q - Quit
""")


def show_action_menu():
    print("""
Actions:
1 - Open hand fully
2 - Close hand fully
3 - Half open hand
4 - Set custom opening value
5 - Show hand status
b - Back
""")


def get_grippers(reachy):
    left = safe_call("Access left gripper", lambda: reachy.l_arm.gripper)
    right = safe_call("Access right gripper", lambda: reachy.r_arm.gripper)
    return left, right


def show_status(gripper, name):
    print(f"\n===== {name} hand status =====")
    print(gripper)

    possible_attrs = [
        "opening",
        "present_opening",
        "goal_opening",
        "is_on",
        "is_off",
        "compliant",
    ]

    for attr in possible_attrs:
        if hasattr(gripper, attr):
            safe_call(f"{name}.{attr}", lambda attr=attr: getattr(gripper, attr))


def show_functions(gripper, name):
    print(f"\n===== {name} hand available functions =====")
    attrs = [a for a in dir(gripper) if not a.startswith("_")]

    for attr in attrs:
        print("-", attr)


def set_opening(gripper, name, value):
    """
    Most Reachy gripper APIs use:
    0   = closed
    100 = fully open
    """
    value = max(0, min(100, value))

    if hasattr(gripper, "set_opening"):
        safe_call(f"{name} set_opening({value})", lambda: gripper.set_opening(value))
    elif hasattr(gripper, "goto"):
        safe_call(f"{name} goto({value})", lambda: gripper.goto(value))
    else:
        print(f"[FAILED] {name} has no set_opening() or goto() method.")


def apply_to_hand(hand_choice, left, right, action_func):
    if hand_choice == "1":
        action_func(left, "Left")
    elif hand_choice == "2":
        action_func(right, "Right")
    elif hand_choice == "3":
        action_func(left, "Left")
        action_func(right, "Right")
    else:
        print("Invalid hand choice.")


def control_hand(hand_choice, left, right):
    while True:
        show_action_menu()
        action = input("Choose action: ").strip().lower()

        if action == "1":
            apply_to_hand(hand_choice, left, right, lambda g, n: set_opening(g, n, 100))

        elif action == "2":
            confirm = input("Close hand fully? Type yes to continue: ").strip().lower()
            if confirm == "yes":
                apply_to_hand(hand_choice, left, right, lambda g, n: set_opening(g, n, 0))
            else:
                print("Cancelled.")

        elif action == "3":
            apply_to_hand(hand_choice, left, right, lambda g, n: set_opening(g, n, 50))

        elif action == "4":
            try:
                value = int(input("Enter opening value 0-100: ").strip())
                apply_to_hand(hand_choice, left, right, lambda g, n: set_opening(g, n, value))
            except ValueError:
                print("Please enter a number from 0 to 100.")

        elif action == "5":
            apply_to_hand(hand_choice, left, right, show_status)

        elif action == "b":
            break

        else:
            print("Invalid action.")

        time.sleep(0.5)


def main():
    print("Connecting to Reachy...")
    reachy = ReachySDK(host=ROBOT_HOST)

    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        print("Cannot connect to Reachy. Check IP/network/core.")
        return

    safe_call("Turn robot on", lambda: reachy.turn_on())

    left, right = get_grippers(reachy)

    if left is None and right is None:
        print("No hand/gripper objects available.")
        return

    while True:
        show_gripper_menu()
        choice = input("Choose option: ").strip().lower()

        if choice in ["1", "2", "3"]:
            control_hand(choice, left, right)

        elif choice == "4":
            if left is not None:
                show_status(left, "Left")
            if right is not None:
                show_status(right, "Right")

        elif choice == "5":
            if left is not None:
                show_functions(left, "Left")
            if right is not None:
                show_functions(right, "Right")

        elif choice == "q":
            print("Exiting hand controller.")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()