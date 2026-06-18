# record_poses.py

import numpy as np

from reachy2_sdk import ReachySDK

from config import ROBOT_HOST
from motion_paper import get_selected_arm


def print_pose(name, pose):
    """
    Print 4x4 pose in copy-paste format.
    """

    pose = np.array(pose, dtype=np.float64)

    print()
    print(f"{name} = np.array([")
    for row in pose:
        print("    [" + ", ".join(f"{value: .6f}" for value in row) + "],")
    print("], dtype=np.float64)")
    print()


def main():
    reachy = ReachySDK(host=ROBOT_HOST)

    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy.")

    print("Connected to Reachy.")

    reachy.turn_on()

    arm = get_selected_arm(reachy)

    print()
    print("Use this script to record real 4x4 pose matrices.")
    print("Move Reachy to each pose safely, then press Enter.")
    print()

    pose_names = [
        "HOME_POSE",
        "PRE_GRASP_POSE",
        "GRASP_POSE",
        "LIFT_POSE",
        "HANDOVER_POSE"
    ]

    for pose_name in pose_names:
        input(f"Move Reachy to {pose_name}, then press Enter... ")

        pose = arm.forward_kinematics()

        print_pose(pose_name, pose)

    print("Copy the printed matrices into motion_paper.py.")


if __name__ == "__main__":
    main()