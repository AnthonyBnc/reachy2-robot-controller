import numpy as np
from reachy2_sdk import ReachySDK


ROBOT_HOST = "10.116.19.109"


def print_pose(name, pose):
    pose = np.array(pose, dtype=np.float64)

    print()
    print(f"{name} = np.array([")
    for row in pose:
        print("    [" + ", ".join(f"{value: .6f}" for value in row) + "],")
    print("], dtype=np.float64)")
    print()


def main():
    reachy = ReachySDK(host=ROBOT_HOST)

    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy.")

    # IMPORTANT:
    # Do NOT call reachy.turn_on() here.
    # turn_on() makes the motors stiff and hard to move manually.

    arm = reachy.r_arm

    if arm is None:
        raise RuntimeError("Right arm is not available.")

    print()
    print("Pose recording mode.")
    print("Do NOT force the arm if it feels locked.")
    print()
    print("Before each recording:")
    print("1. Use the dashboard to make the right arm free/compliant/torque-off.")
    print("2. Move the right hand to the desired pose.")
    print("3. Press Enter here to read the current 4x4 matrix.")
    print()

    pose_names = [
        "BASE_POSE",
        "PRE_GRASP_POSE",
        "GRASP_POSE",
        "LIFT_POSE",
        "HANDOVER_POSE",
    ]

    for pose_name in pose_names:
        input(f"Move Reachy to {pose_name}, then press Enter... ")

        pose = arm.forward_kinematics()
        print_pose(pose_name, pose)

    print("Done. Copy these matrices into your replay script.")


if __name__ == "__main__":
    main()