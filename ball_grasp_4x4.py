import time
import numpy as np
from reachy2_sdk import ReachySDK


ROBOT_HOST = "10.116.19.109"


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def print_matrix(name, matrix):
    print(f"\n{name}:")
    print(np.array2string(matrix, precision=4, suppress_small=True))


def validate_pose_matrix(pose):
    pose = np.array(pose, dtype=np.float64)

    if pose.shape != (4, 4):
        raise ValueError("Pose must be a 4x4 matrix.")

    if not np.all(np.isfinite(pose)):
        raise ValueError("Pose contains NaN or infinite values.")

    if not np.allclose(pose[3, :], [0, 0, 0, 1]):
        raise ValueError("Last row must be [0, 0, 0, 1].")

    return pose


def move_4x4(arm, pose, duration=2.0):
    """
    Move Reachy right arm using 4x4 matrix.

    Important:
    This version is compatible with reachy2-sdk==1.0.7.
    Do not use interpolation_space or interpolation_mode.
    """

    pose = validate_pose_matrix(pose)

    print_matrix("Moving to 4x4 pose", pose)

    arm.goto(
        pose,
        duration=duration,
        wait=True
    )


def translate_pose_robot_frame(base_pose, dx=0.0, dy=0.0, dz=0.0):
    """
    Translate a 4x4 pose in robot/world frame.

    Approximate meaning:
        dx positive = forward
        dx negative = backward

        dy positive = robot left
        dy negative = robot right

        dz positive = up
        dz negative = down
    """

    new_pose = np.array(base_pose, dtype=np.float64).copy()

    new_pose[0, 3] += dx
    new_pose[1, 3] += dy
    new_pose[2, 3] += dz

    return new_pose


def open_gripper(arm):
    if arm.gripper is None:
        raise RuntimeError("Right gripper is not available.")

    print("Opening right gripper...")
    arm.gripper.set_opening(100)
    time.sleep(0.8)


def close_gripper_for_ball(arm):
    if arm.gripper is None:
        raise RuntimeError("Right gripper is not available.")

    print("Closing gripper for ball...")

    # Tune this depending on ball size.
    # 100 = fully open
    # 0 = fully closed
    arm.gripper.set_opening(25)

    time.sleep(1.0)


def safe_stop_message():
    print()
    print("Safety reminder:")
    print("- Keep E-stop nearby.")
    print("- Make sure the arm has free space.")
    print("- Start with very small dx/dy/dz values.")
    print("- Do not use mobile base.")


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    safe_stop_message()

    reachy = ReachySDK(host=ROBOT_HOST)

    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy.")

    reachy.turn_on()

    arm = reachy.r_arm

    if arm is None:
        raise RuntimeError("Right arm is not available.")

    if arm.gripper is None:
        raise RuntimeError("Right gripper is not available.")

    print()
    print("Before continuing:")
    print("1. Use the dashboard to move Reachy's right arm to the 90-degree default pose.")
    print("2. Place the ball in front of the right hand.")
    print("3. Make sure the arm path is clear.")
    print()

    input("When ready, press Enter... ")

    # -----------------------------------------------------
    # 1. Read current dashboard-set 4x4 pose
    # -----------------------------------------------------

    base_pose = arm.forward_kinematics()
    base_pose = np.array(base_pose, dtype=np.float64)

    print_matrix("BASE_POSE from dashboard 90-degree position", base_pose)

    # -----------------------------------------------------
    # 2. Create relative 4x4 poses
    # -----------------------------------------------------
    # Start small.
    # If the hand does not reach the ball, slowly increase dx.
    # If the hand is too high/low, adjust dz.
    # If the hand is too left/right, adjust dy.
    # -----------------------------------------------------

    pre_grasp_pose = translate_pose_robot_frame(
        base_pose,
        dx=0.04,
        dy=0.00,
        dz=0.00
    )

    grasp_pose = translate_pose_robot_frame(
        pre_grasp_pose,
        dx=0.04,
        dy=0.00,
        dz=0.00
    )

    lift_pose = translate_pose_robot_frame(
        grasp_pose,
        dx=0.00,
        dy=0.00,
        dz=0.10
    )

    return_pose = base_pose.copy()

    print_matrix("PRE_GRASP_POSE", pre_grasp_pose)
    print_matrix("GRASP_POSE", grasp_pose)
    print_matrix("LIFT_POSE", lift_pose)
    print_matrix("RETURN_POSE", return_pose)

    confirm = input("Run movement? Type yes to continue: ")

    if confirm.lower().strip() != "yes":
        print("Cancelled before movement.")
        return

    # -----------------------------------------------------
    # 3. Execute ball grasp sequence
    # -----------------------------------------------------

    open_gripper(arm)

    print("Moving to pre-grasp pose...")
    move_4x4(arm, pre_grasp_pose, duration=2.5)

    print("Moving to grasp pose...")
    move_4x4(arm, grasp_pose, duration=2.0)

    close_gripper_for_ball(arm)

    print("Lifting ball...")
    move_4x4(arm, lift_pose, duration=2.0)

    input("Press Enter to return to base pose... ")

    print("Returning to base pose...")
    move_4x4(arm, return_pose, duration=2.5)

    print("Done.")


if __name__ == "__main__":
    main()