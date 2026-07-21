# robot/motion.py

import time
import numpy as np

from config import SAFETY_PAUSES
from robot.poses import (
    BASE_POSE,
    PRE_GRASP_POSE,
    GRASP_POSE,
    LIFT_POSE,
    HANDOVER_POSE,
)


def wait_if_safety(message):
    if SAFETY_PAUSES:
        input(message)


def validate_pose_matrix(pose):
    pose = np.array(pose, dtype=np.float64)

    if pose.shape != (4, 4):
        raise ValueError("Pose must be a 4x4 matrix.")

    if not np.all(np.isfinite(pose)):
        raise ValueError("Pose contains NaN or infinite values.")

    if not np.allclose(pose[3, :], [0, 0, 0, 1]):
        raise ValueError("Last row must be [0, 0, 0, 1].")

    return pose


def move_4x4(arm, pose, duration=3.0):
    pose = validate_pose_matrix(pose)

    print()
    print("Moving to pose:")
    print(np.array2string(pose, precision=4, suppress_small=True))
    print(f"x={pose[0, 3]:.3f}, y={pose[1, 3]:.3f}, z={pose[2, 3]:.3f}")

    arm.goto(
        pose,
        duration=duration,
        wait=True,
    )


def open_gripper(arm):
    if arm.gripper is None:
        print("No gripper found.")
        return

    print("Opening gripper...")
    arm.gripper.set_opening(100)
    time.sleep(0.8)


def close_gripper_for_ball(arm, opening=25):
    if arm.gripper is None:
        print("No gripper found.")
        return

    print(f"Closing gripper to {opening}...")
    arm.gripper.set_opening(opening)
    time.sleep(1.0)


def look_forward(reachy):
    if reachy is None:
        return

    try:
        reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.0)
    except Exception as e:
        print("look_forward skipped:", e)


def nod(reachy):
    if reachy is None:
        return

    try:
        reachy.head.look_at(x=0.5, y=0.0, z=0.08, duration=0.6)
        reachy.head.look_at(x=0.5, y=0.0, z=-0.06, duration=0.6)
        reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=0.6)
    except Exception as e:
        print("nod skipped:", e)


def greeting_hand(reachy):
    if reachy is None:
        return

    try:
        if reachy.r_arm.gripper is not None:
            reachy.r_arm.gripper.set_opening(100)
            time.sleep(0.5)
            reachy.r_arm.gripper.set_opening(60)
            time.sleep(0.5)
    except Exception as e:
        print("greeting_hand skipped:", e)


def grasp_handover_release(reachy, label="grasp"):
    if reachy is None:
        print(f"Skipping {label}: Reachy not connected.")
        return

    arm = reachy.r_arm

    if arm is None:
        print("Right arm not available.")
        return

    if arm.gripper is None:
        print("Right gripper not available.")
        return

    print()
    print(f"Starting {label} sequence.")
    print("Make sure the ball is in the same position as the recorded poses.")

    wait_if_safety("Press Enter to start movement... ")

    open_gripper(arm)

    move_4x4(arm, BASE_POSE, duration=4.0)
    move_4x4(arm, PRE_GRASP_POSE, duration=4.0)

    wait_if_safety("Check PRE_GRASP_POSE. Press Enter to continue to GRASP_POSE... ")

    move_4x4(arm, GRASP_POSE, duration=3.0)

    wait_if_safety("Check gripper around ball. Press Enter to close gripper... ")

    close_gripper_for_ball(arm, opening=25)

    wait_if_safety("Press Enter to lift... ")

    move_4x4(arm, LIFT_POSE, duration=3.0)
    move_4x4(arm, HANDOVER_POSE, duration=4.0)

    wait_if_safety("Press Enter to open gripper and release ball... ")

    open_gripper(arm)
    time.sleep(1.0)

    wait_if_safety("Press Enter to return to BASE_POSE... ")

    move_4x4(arm, BASE_POSE, duration=4.0)

    print(f"{label} sequence complete.")