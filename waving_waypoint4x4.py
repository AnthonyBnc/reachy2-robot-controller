from reachy2_sdk import ReachySDK
import numpy as np
import time

ROBOT_HOST = "10.116.19.109"

SIDE_MOVE = 0.010
UP_MOVE = 0.005
DURATION = 1.5
REPEAT = 2


def check_ik(arm, target_matrix, name):
    try:
        current_joints = arm.get_current_positions()
        arm.inverse_kinematics(target_matrix, q0=current_joints)
        print(f"IK passed: {name}")
        return True
    except TypeError:
        try:
            arm.inverse_kinematics(target_matrix)
            print(f"IK passed without q0: {name}")
            return True
        except Exception as e:
            print(f"IK failed: {name}")
            print(e)
            return False
    except Exception as e:
        print(f"IK failed: {name}")
        print(e)
        return False


def make_offset_matrix(base_matrix, dx=0.0, dy=0.0, dz=0.0):
    target = base_matrix.copy()
    target[0, 3] += dx
    target[1, 3] += dy
    target[2, 3] += dz
    return target


def goto_matrix(arm, target_matrix, name):
    print(f"\nMoving to {name}")
    print(np.round(target_matrix, 4))

    if not check_ik(arm, target_matrix, name):
        print("Blocked: IK failed.")
        return False

    arm.goto(target_matrix, duration=DURATION, wait=True)
    print(f"Finished: {name}")
    return True


def main():
    print("Step 1: Connecting...")
    reachy = ReachySDK(host=ROBOT_HOST)

    print("Step 2: Checking connection...")
    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy")

    print("Connected to Reachy.")
    print("Skipping reachy.turn_on() for this debug test.")
    print("Keep E-stop nearby.")

    arm = reachy.r_arm

    print("Step 3: Reading current joints...")
    current_joints = arm.get_current_positions()
    print("Current joints:", current_joints)

    print("Step 4: Getting current 4x4 matrix...")
    center_matrix = arm.forward_kinematics(current_joints)
    print("Current hand matrix:")
    print(np.round(center_matrix, 4))

    up_matrix = make_offset_matrix(center_matrix, dz=UP_MOVE)
    left_matrix = make_offset_matrix(center_matrix, dy=SIDE_MOVE, dz=UP_MOVE)
    right_matrix = make_offset_matrix(center_matrix, dy=-SIDE_MOVE, dz=UP_MOVE)

    print("Step 5: Prechecking IK...")
    for name, matrix in [
        ("up", up_matrix),
        ("left", left_matrix),
        ("right", right_matrix),
        ("center", center_matrix),
    ]:
        if not check_ik(arm, matrix, name):
            print("At least one matrix failed IK. Robot will not move.")
            return

    print("Step 6: Starting wave in 3 seconds...")
    time.sleep(3)

    goto_matrix(arm, up_matrix, "up")

    for i in range(REPEAT):
        print(f"Wave {i + 1}/{REPEAT}")
        goto_matrix(arm, left_matrix, "left")
        goto_matrix(arm, right_matrix, "right")

    goto_matrix(arm, center_matrix, "return_to_start")

    print("Done.")


if __name__ == "__main__":
    main()