# main.py

import time
import cv2

from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView

from config import (
    ROBOT_HOST,
    CAMERA_SIDE,
    SHOW_DEBUG_WINDOW,
    REQUIRED_STABLE_FRAMES,
    MESSAGE
)

from vision_paper import (
    detect_paper,
    is_inside_pickup_zone,
    draw_debug
)

from motion_paper import (
    get_selected_arm,
    go_home,
    grasp_paper_sequence
)

from speech import say_message


def get_camera_view():
    """
    Select Reachy camera view.
    """

    side = CAMERA_SIDE.lower().strip()

    if side == "left":
        return CameraView.LEFT

    if side == "right":
        return CameraView.RIGHT

    raise ValueError("CAMERA_SIDE must be 'left' or 'right'.")


def get_camera_frame(reachy):
    """
    Get frame from Reachy's teleop camera.
    """

    camera_view = get_camera_view()

    result = reachy.cameras.teleop.get_frame(camera_view)

    if result is None:
        return None

    if isinstance(result, tuple):
        frame = result[0]
    else:
        frame = result

    return frame


def wait_until_paper_ready(reachy):
    """
    Wait until paper is detected inside pickup zone.
    """

    stable_count = 0

    print("Looking for paper...")
    print("Put the paper inside the blue pickup zone.")
    print("Press G to force grasp.")
    print("Press Q to quit.")

    while True:
        frame = get_camera_frame(reachy)

        if frame is None:
            print("No camera frame received.")
            time.sleep(0.2)
            continue

        paper = detect_paper(frame)

        if paper is not None and is_inside_pickup_zone(paper, frame):
            stable_count += 1
            print(
                f"Paper stable: {stable_count}/{REQUIRED_STABLE_FRAMES}",
                end="\r"
            )
        else:
            stable_count = 0

        if SHOW_DEBUG_WINDOW:
            debug_frame = draw_debug(
                frame,
                paper,
                stable_count,
                REQUIRED_STABLE_FRAMES
            )

            cv2.imshow("Reachy Paper Detection", debug_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("\nProgram stopped.")
                return False

            if key == ord("g"):
                print("\nForce grasp triggered.")
                return True

        else:
            time.sleep(0.05)

        if stable_count >= REQUIRED_STABLE_FRAMES:
            print("\nPaper detected inside pickup zone.")
            return True


def main():
    reachy = ReachySDK(host=ROBOT_HOST)

    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy. Check ROBOT_HOST.")

    print("Connected to Reachy.")

    reachy.turn_on()
    print("Reachy turned on.")

    arm = get_selected_arm(reachy)

    if arm.gripper is None:
        raise RuntimeError("Selected arm has no gripper.")

    try:
        go_home(arm)

        paper_ready = wait_until_paper_ready(reachy)

        if not paper_ready:
            print("Demo stopped before grasping.")
            return

        print("Paper ready. Starting movement.")
        grasp_paper_sequence(arm)

        print("Reading message.")
        say_message(MESSAGE)

        print("Demo complete.")

    finally:
        if SHOW_DEBUG_WINDOW:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()