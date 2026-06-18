import time
import numpy as np

from reachy2_sdk import ReachySDK


ROBOT_HOST = "10.116.19.109"


def print_matrix(name, matrix):
    print(f"\n{name}:")
    print(np.array2string(matrix, precision=4, suppress_small=True))

def validate_pose_matrix(pose):
    if not isinstance(pose, np.ndarray):
        raise TypeError("Oise must be a NumPy array.")

    if pose.shape != (4, 4):
        raise ValueError("Pose Must be a 4x4 matrix.")

    if not np.all(np.isfinite(pose)):
        raise ValueError("Pose contains NaN or infinite values.")

    if not np.allclose(pose[3, :], [0, 0, 0, 1]):
        raise ValueError("Last row must be [0, 0, 0, 1].")

def move_4x4(arm, pose, duration  =2.0):
    validate_pose_matrix(pose)

    print_matrix("Moving to", pose)

    arm.goto(
        pose, 
        duration = duration, 
        wait = True, 
        interpolation_space = "cartesian_space",
        interpolation_mode = "minimum_jerk"
    )

def translate_pose_robot_frame(base_pose, dx=0.0, dy=0.0, dz=0.0):
    new_pose = base_pose.copy()

    new_pose[0, 3] += dx
    new_pose[1, 3] += dy
    new_pose[2, 3] += dz

    return new_pose

def open_gripper(arm):
    if arm.gripper is None: 
        raise RuntimeError("Right arm has no gripper.")

    print("Opening gripper...")
    arm.gripper.set_opening(100.0)
    time.sleep(0.5)

def close_gripper_for_ball(arm):
    if arm.gripper is None: 
        raise RuntimeError("Right arm has no gripper.")

    print("Closing gripper...")
    arm.gripper.set_opening(15.0)
    time.sleep(1.0)

def main():
    reachy = ReachySDK(host=ROBOT_HOST)

    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy")
    
    print("Connected to Reachy.")

    reachy.turn_on()
    
    arm = reachy.r_arm

    if arm is None: 
        raise RuntimeError("Right arm is not available.")
    
    if arm.gripper is None: 
        raise RuntimeError("Right arm has no gripper.")

    input("Move Reachy to 90 degree pose")
    base_pose = arm.forward_kinematics()
    base_pose = np.arrya(base_pose, dtype=np.float64)

    print_matrix("Base 90 degree 4x4 pose", base_pose)

    ########## BALL GRASP POSES ##########  
    pre_grasp_pose = translate_pose_robot_frame(
        base_pose,
        dx=0.06,
        dy=0.00,
        dz=-0.02
    )

    grasp_pose = translate_pose_robot_frame(
        pre_grasp_pose,
        dx=0.06,
        dy=0.00,
        dz=0.00
    )

    lift_pose = translate_pose_robot_frame(
        grasp_pose,
        dx=0.00,
        dy=0.00,
        dz=0.12
    )

    handover_pose = translate_pose_robot_frame(
        lift_pose,
        dx=0.05,
        dy=0.08,
        dz=0.02
    )

    print_matrix("PRE_GRASP_POSE", pre_grasp_pose)
    print_matrix("GRASP_POSE", grasp_pose)
    print_matrix("LIFT_POSE", lift_pose)
    print_matrix("HANDOVER_POSE", handover_pose)

    open_gripper(arm)

    print("Moving to pre-grasp pose...")
    move_4x4(arm, pre_grasp_pose, duration=2.0)

    print("Moving to grasp pose...")
    move_4x4(arm, grasp_pose, duration=1.5)

    close_gripper_for_ball(arm)

    print("Lifting ball...")
    move_4x4(arm, lift_pose, duration=1.5)

    print("Moving to handover pose...")
    move_4x4(arm, handover_pose, duration=2.0)

    print("Ball grasp sequence complete.")


if __name__ == "__main__":
    main()