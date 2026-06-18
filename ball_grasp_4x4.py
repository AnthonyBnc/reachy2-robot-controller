import time
import numpy as np
from reachy2_sdk import ReachySDK


ROBOT_HOST = "10.116.19.109"


BASE_POSE = np.array([
    [ 0.860772,  0.508543, -0.021341, -0.017208],
    [-0.506423,  0.851472, -0.136128, -0.125997],
    [-0.051056,  0.127982,  0.990461, -0.655444],
    [ 0.000000,  0.000000,  0.000000,  1.000000],
], dtype=np.float64)


PRE_GRASP_POSE = np.array([
    [ 0.035190,  0.157996, -0.986813,  0.368299],
    [-0.198593,  0.968838,  0.148036, -0.196380],
    [ 0.979450,  0.190764,  0.065470, -0.310717],
    [ 0.000000,  0.000000,  0.000000,  1.000000],
], dtype=np.float64)


GRASP_POSE = np.array([
    [ 0.256353,  0.027002, -0.966206,  0.485983],
    [-0.080179,  0.996759,  0.006583, -0.198659],
    [ 0.963252,  0.075782,  0.257687, -0.382602],
    [ 0.000000,  0.000000,  0.000000,  1.000000],
], dtype=np.float64)


LIFT_POSE = np.array([
    [-0.050080,  0.055257, -0.997215,  0.466367],
    [-0.077167,  0.995269,  0.059024, -0.234385],
    [ 0.995760,  0.079909, -0.045580, -0.253058],
    [ 0.000000,  0.000000,  0.000000,  1.000000],
], dtype=np.float64)


HANDOVER_POSE = np.array([
    [-0.022118, -0.093386, -0.995384,  0.618968],
    [-0.097624,  0.991071, -0.090812, -0.175339],
    [ 0.994978,  0.095165, -0.031037, -0.138446],
    [ 0.000000,  0.000000,  0.000000,  1.000000],
], dtype=np.float64)


def validate_pose_matrix(pose):
    pose = np.array(pose, dtype=np.float64)

    if pose.shape != (4, 4):
        raise ValueError("Pose must be a 4x4 matrix.")

    if not np.all(np.isfinite(pose)):
        raise ValueError("Pose contains NaN or infinite values.")

    if not np.allclose(pose[3, :], [0, 0, 0, 1]):
        raise ValueError("Last row must be [0, 0, 0, 1].")

    return pose


def print_pose_position(name, pose):
    print()
    print(name)
    print(np.array2string(pose, precision=4, suppress_small=True))
    print(f"x={pose[0, 3]:.3f}, y={pose[1, 3]:.3f}, z={pose[2, 3]:.3f}")


def move_4x4(arm, pose, duration=3.0):
    """
    Reachy SDK 1.0.7 compatible movement.
    Do not use interpolation_space or interpolation_mode here.
    """

    pose = validate_pose_matrix(pose)
    print_pose_position("Moving to pose:", pose)

    arm.goto(
        pose,
        duration=duration,
        wait=True
    )


def open_gripper(arm):
    if arm.gripper is None:
        raise RuntimeError("Right gripper is not available.")

    print("Opening gripper...")
    arm.gripper.set_opening(100)
    time.sleep(0.8)


def close_gripper_for_ball(arm, opening=25):
    if arm.gripper is None:
        raise RuntimeError("Right gripper is not available.")

    print(f"Closing gripper to {opening}...")
    arm.gripper.set_opening(opening)
    time.sleep(1.0)


def main():
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
    print("Before starting:")
    print("1. Put the ball in the exact same position as when you recorded the poses.")
    print("2. Keep the E-stop nearby.")
    print("3. Make sure the right arm path is clear.")
    print("4. First test with no ball or with a soft ball.")
    print()

    confirm = input("Type yes to start the replay: ").strip().lower()

    if confirm != "yes":
        print("Cancelled.")
        return

    open_gripper(arm)

    print("Moving to BASE_POSE...")
    move_4x4(arm, BASE_POSE, duration=4.0)

    print("Moving to PRE_GRASP_POSE...")
    move_4x4(arm, PRE_GRASP_POSE, duration=4.0)

    input("Check position. Press Enter to continue to GRASP_POSE... ")

    print("Moving to GRASP_POSE...")
    move_4x4(arm, GRASP_POSE, duration=3.0)

    input("Check gripper around ball. Press Enter to close gripper... ")

    close_gripper_for_ball(arm, opening=25)

    input("Press Enter to lift... ")

    print("Moving to LIFT_POSE...")
    move_4x4(arm, LIFT_POSE, duration=3.0)

    input("Press Enter to move to HANDOVER_POSE... ")

    print("Moving to HANDOVER_POSE...")
    move_4x4(arm, HANDOVER_POSE, duration=4.0)

    input("Press Enter to return to BASE_POSE... ")

    print("Returning to BASE_POSE...")
    move_4x4(arm, BASE_POSE, duration=4.0)

    open_gripper(arm)
    time.sleep(1.0)

    move_4x4(arm, GRASP_POSE, duration=3.0)
    move_4x4(arm, PRE_GRASP_POSE, duration=4.0)
    move_4x4(arm, BASE_POSE, duration=4.0)

    print("Done.")


if __name__ == "__main__":
    main()