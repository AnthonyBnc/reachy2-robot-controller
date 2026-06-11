import time
from dataclasses import dataclass
from typing import Optional, Literal


ArmName = Literal["r_arm", "l_arm"]


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


@dataclass
class ArmWaypoint:
    name: str
    arm: ArmName
    deltas: list[float]
    duration: float = 2.0
    wait: bool = True
    gripper_opening: Optional[int] = None


@dataclass
class HeadWaypoint:
    name: str
    x: float = 0.5
    y: float = 0.0
    z: float = 0.0
    duration: float = 1.5


@dataclass
class PauseWaypoint:
    name: str
    seconds: float = 1.0


class WaypointController:
    """
    Safe waypoint controller for Reachy 2.

    Current scope:
    - Head movement
    - Right arm movement
    - Left arm movement
    - Gripper opening
    - Pause timing

    Mobile base is intentionally not included.
    """

    MAX_DELTAS = [
        25,  # shoulder pitch
        30,  # shoulder roll
        20,  # elbow yaw
        30,  # elbow pitch
        25,  # wrist roll
        20,  # wrist pitch
        30,  # wrist yaw
    ]

    def __init__(self, reachy):
        self.reachy = reachy

    def get_arm(self, arm_name: ArmName):
        if arm_name == "r_arm":
            return self.reachy.r_arm
        if arm_name == "l_arm":
            return self.reachy.l_arm
        raise ValueError(f"Unknown arm name: {arm_name}")

    def safe_relative_pose(self, current, deltas):
        if len(deltas) != 7:
            raise ValueError("Arm waypoint must contain exactly 7 joint deltas.")

        target = current.copy()

        for i in range(7):
            safe_delta = clamp(
                deltas[i],
                -self.MAX_DELTAS[i],
                self.MAX_DELTAS[i],
            )
            target[i] = current[i] + safe_delta

        return target

    def run_arm_waypoint(self, waypoint: ArmWaypoint):
        print(f"Running arm waypoint: {waypoint.name}")

        arm = self.get_arm(waypoint.arm)
        current = arm.get_current_positions()

        target = self.safe_relative_pose(current, waypoint.deltas)

        arm.goto(
            target,
            duration=waypoint.duration,
            wait=waypoint.wait,
        )

        if waypoint.gripper_opening is not None:
            try:
                arm.gripper.set_opening(waypoint.gripper_opening)
            except Exception as e:
                print(f"Gripper not available: {e}")

    def run_head_waypoint(self, waypoint: HeadWaypoint):
        print(f"Running head waypoint: {waypoint.name}")

        safe_x = clamp(waypoint.x, 0.4, 0.7)
        safe_y = clamp(waypoint.y, -0.25, 0.25)
        safe_z = clamp(waypoint.z, -0.15, 0.20)
        safe_duration = clamp(waypoint.duration, 0.5, 3.0)

        self.reachy.head.look_at(
            x=safe_x,
            y=safe_y,
            z=safe_z,
            duration=safe_duration,
        )

    def run_pause(self, waypoint: PauseWaypoint):
        print(f"Pause: {waypoint.seconds} seconds")
        time.sleep(waypoint.seconds)

    def run_sequence(self, waypoints):
        """
        Run a list of waypoints in order.
        """

        for waypoint in waypoints:
            if isinstance(waypoint, ArmWaypoint):
                self.run_arm_waypoint(waypoint)

            elif isinstance(waypoint, HeadWaypoint):
                self.run_head_waypoint(waypoint)

            elif isinstance(waypoint, PauseWaypoint):
                self.run_pause(waypoint)

            else:
                raise TypeError(f"Unsupported waypoint type: {type(waypoint)}")