# motion_paper.py

import time
import numpy as np

from config import ARM_SIDE


def make_pose(x, y, z, roll=0.0, pitch=0.0, yaw=0.0, degrees=True):
    """
    Create a 4x4 transformation matrix.

    x, y, z:
        End-effector position.

    roll, pitch, yaw:
        End-effector rotation.
    """

    if degrees:
        roll = np.deg2rad(roll)
        pitch = np.deg2rad(pitch)
        yaw = np.deg2rad(yaw)

    rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ], dtype=np.float64)

    ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ], dtype=np.float64)

    rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ], dtype=np.float64)

    rotation = rz @ ry @ rx

    pose = np.eye(4, dtype=np.float64)
    pose[:3, :3] = rotation
    pose[0, 3] = x
    pose[1, 3] = y
    pose[2, 3] = z

    return pose


# ==========================================================
# PLACEHOLDER 4x4 POSES
# Replace these after running record_poses.py
# ==========================================================

HOME_POSE = make_pose(
    x=0.25,
    y=-0.25,
    z=0.30,
    roll=0,
    pitch=70,
    yaw=0
)

PRE_GRASP_POSE = make_pose(
    x=0.35,
    y=-0.25,
    z=0.16,
    roll=0,
    pitch=90,
    yaw=0
)

GRASP_POSE = make_pose(
    x=0.42,
    y=-0.25,
    z=0.09,
    roll=0,
    pitch=90,
    yaw=0
)

LIFT_POSE = make_pose(
    x=0.36,
    y=-0.25,
    z=0.26,
    roll=0,
    pitch=90,
    yaw=0
)

HANDOVER_POSE = make_pose(
    x=0.42,
    y=-0.05,
    z=0.28,
    roll=0,
    pitch=75,
    yaw=0
)


def get_selected_arm(reachy):
    """
    Select right or left arm.
    """

    side = ARM_SIDE.lower().strip()

    if side == "r":
        arm = reachy.r_arm
    elif side == "l":
        arm = reachy.l_arm
    else:
        raise ValueError("ARM_SIDE must be 'r' or 'l'.")

    if arm is None:
        raise RuntimeError(f"Arm '{ARM_SIDE}' is not available.")

    return arm


def validate_pose_matrix(pose_matrix):
    """
    Validate 4x4 pose matrix before sending to robot.
    """

    if not isinstance(pose_matrix, np.ndarray):
        raise TypeError("Pose must be a NumPy array.")

    if pose_matrix.shape != (4, 4):
        raise ValueError("Pose must be a 4x4 matrix.")

    if not np.all(np.isfinite(pose_matrix)):
        raise ValueError("Pose contains NaN or infinite values.")

    if not np.allclose(pose_matrix[3, :], [0, 0, 0, 1]):
        raise ValueError("Last row of pose must be [0, 0, 0, 1].")


def move_arm_cartesian(arm, pose_matrix, duration=2.0, wait=True):
    """
    Move arm using 4x4 Cartesian matrix.
    """

    validate_pose_matrix(pose_matrix)

    print("Moving to 4x4 pose:")
    print(np.array2string(pose_matrix, precision=4, suppress_small=True))

    arm.goto(
        pose_matrix,
        duration=duration,
        wait=wait,
        interpolation_space="cartesian_space",
        interpolation_mode="minimum_jerk"
    )


def open_gripper(arm):
    """
    Open gripper.
    """

    if arm.gripper is None:
        raise RuntimeError("No gripper found on selected arm.")

    print("Opening gripper...")
    arm.gripper.set_opening(100.0)
    time.sleep(0.5)


def close_gripper_for_paper(arm):
    """
    Close gripper gently for paper.
    """

    if arm.gripper is None:
        raise RuntimeError("No gripper found on selected arm.")

    print("Closing gripper...")
    arm.gripper.set_opening(15.0)
    time.sleep(0.8)


def go_home(arm):
    """
    Move to home pose.
    """

    print("Going home...")
    move_arm_cartesian(
        arm,
        HOME_POSE,
        duration=2.0,
        wait=True
    )


def grasp_paper_sequence(arm):
    """
    Full paper grasp and handover sequence.
    """

    print("Starting grasp sequence...")

    open_gripper(arm)

    print("Moving to pre-grasp pose...")
    move_arm_cartesian(
        arm,
        PRE_GRASP_POSE,
        duration=2.0,
        wait=True
    )

    print("Moving to grasp pose...")
    move_arm_cartesian(
        arm,
        GRASP_POSE,
        duration=1.5,
        wait=True
    )

    close_gripper_for_paper(arm)

    print("Lifting paper...")
    move_arm_cartesian(
        arm,
        LIFT_POSE,
        duration=1.5,
        wait=True
    )

    print("Moving to handover pose...")
    move_arm_cartesian(
        arm,
        HANDOVER_POSE,
        duration=2.0,
        wait=True
    )

    print("Handover pose reached.")