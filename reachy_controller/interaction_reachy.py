from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView
import cv2
import time


# =========================
# CONFIG
# =========================

ROBOT_HOST = "10.116.19.109"

ENABLE_ARM_GESTURE = True

HEAD_MOVE_COOLDOWN = 0.6
FACE_CENTER_SECONDS_TO_WAVE = 2.0
WAVE_COOLDOWN = 8.0

# Head movement limit
MAX_HEAD_Y = 0.25
MAX_HEAD_Z_UP = 0.20
MAX_HEAD_Z_DOWN = -0.15

# Face dead zone
FACE_CENTER_DEADZONE_X = 0.15
FACE_CENTER_DEADZONE_Y = 0.15


# =========================
# HELPER FUNCTIONS
# =========================

def safe_call(label, func):
    try:
        result = func()
        print(f"[OK] {label}")
        return result
    except Exception as e:
        print(f"[FAILED] {label}")
        print("Error:", e)
        return None


def connect_reachy():
    print("Connecting to Reachy...")
    reachy = ReachySDK(host=ROBOT_HOST)

    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise ConnectionError("Cannot connect to Reachy. Check IP/network/core service.")

    print("Turning robot on...")
    reachy.turn_on()

    return reachy


def center_head(reachy):
    print("Centering head...")
    safe_call(
        "Head center",
        lambda: reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)
    )


def go_safe_posture(reachy):
    print("Going to default/safe posture...")
    safe_call("Default posture", lambda: reachy.goto_posture())


# =========================
# HEAD TRACKING
# =========================

def move_head_to_track_face(reachy, face_center_x, face_center_y, frame_width, frame_height):
    """
    Tracks the face by moving Reachy's head.
    The camera frame centre is compared with the face centre.
    """

    offset_x = (face_center_x - frame_width / 2) / (frame_width / 2)
    offset_y = (face_center_y - frame_height / 2) / (frame_height / 2)

    # If face is close to centre, do not move
    if abs(offset_x) < FACE_CENTER_DEADZONE_X and abs(offset_y) < FACE_CENTER_DEADZONE_Y:
        return "centered"

    # Convert image offset to Reachy look_at coordinate
    # If face is right side of image, head turns right
    target_y = -MAX_HEAD_Y * offset_x
    target_z = -0.20 * offset_y

    # Limit movement for safety
    target_y = max(-MAX_HEAD_Y, min(MAX_HEAD_Y, target_y))
    target_z = max(MAX_HEAD_Z_DOWN, min(MAX_HEAD_Z_UP, target_z))

    safe_call(
        "Head tracking",
        lambda: reachy.head.look_at(
            x=0.5,
            y=target_y,
            z=target_z,
            duration=0.5
        )
    )

    if offset_x > FACE_CENTER_DEADZONE_X:
        return "face right"
    elif offset_x < -FACE_CENTER_DEADZONE_X:
        return "face left"
    elif offset_y > FACE_CENTER_DEADZONE_Y:
        return "face down"
    elif offset_y < -FACE_CENTER_DEADZONE_Y:
        return "face up"

    return "tracking"


# =========================
# ARM GESTURES
# =========================

def open_right_hand(reachy):
    try:
        reachy.r_arm.gripper.set_opening(100)
        print("[OK] Right hand open")
    except Exception as e:
        print("[INFO] Right gripper not available or failed:", e)


def half_close_right_hand(reachy):
    try:
        reachy.r_arm.gripper.set_opening(40)
        print("[OK] Right hand half close")
    except Exception as e:
        print("[INFO] Right gripper not available or failed:", e)


def right_arm_greeting_wave(reachy):
    """
    Full-arm greeting:
    - Saves current arm position
    - Raises shoulder/elbow slightly
    - Opens hand
    - Waves using wrist yaw
    - Returns arm to original pose

    Joint order:
    0 = shoulder pitch
    1 = shoulder roll
    2 = elbow yaw
    3 = elbow pitch
    4 = wrist roll
    5 = wrist pitch
    6 = wrist yaw
    """

    print("\n=== Greeting wave gesture ===")

    current = safe_call(
        "Read right arm current positions",
        lambda: reachy.r_arm.get_current_positions()
    )

    if current is None:
        print("Cannot wave because right arm position cannot be read.")
        return

    home = current.copy()

    # Create a safe raised arm pose
    raised = current.copy()

    # These are small safe changes. Increase slowly only if needed.
    raised[0] = current[0] - 25   # shoulder pitch
    raised[1] = current[1] + 30   # shoulder roll
    raised[3] = current[3] - 30   # elbow pitch
    raised[5] = current[5] - 5    # wrist pitch
    raised[6] = current[6] + 10   # wrist yaw

    print("Home pose:", home)
    print("Raised pose:", raised)

    input("Press Enter to perform right arm greeting wave. Keep E-stop nearby...")

    # Raise arm
    safe_call(
        "Raise right arm",
        lambda: reachy.r_arm.goto(raised, duration=2.0, wait=True)
    )
    time.sleep(0.5)

    # Open hand
    open_right_hand(reachy)
    time.sleep(0.5)

    # Wave using wrist yaw
    wave_left = raised.copy()
    wave_right = raised.copy()

    wave_left[6] = raised[6] + 25
    wave_right[6] = raised[6] - 25

    safe_call(
        "Wave right 1",
        lambda: reachy.r_arm.goto(wave_left, duration=0.7, wait=True)
    )
    safe_call(
        "Wave right 2",
        lambda: reachy.r_arm.goto(wave_right, duration=0.7, wait=True)
    )
    safe_call(
        "Wave right 3",
        lambda: reachy.r_arm.goto(wave_left, duration=0.7, wait=True)
    )
    safe_call(
        "Wave right 4",
        lambda: reachy.r_arm.goto(wave_right, duration=0.7, wait=True)
    )

    # Return to raised pose first
    safe_call(
        "Return wrist to raised pose",
        lambda: reachy.r_arm.goto(raised, duration=0.8, wait=True)
    )

    # Half close hand
    half_close_right_hand(reachy)
    time.sleep(0.5)

    # Return arm to original pose
    safe_call(
        "Return right arm home",
        lambda: reachy.r_arm.goto(home, duration=2.0, wait=True)
    )

    print("Gesture complete.\n")


def right_arm_small_acknowledge(reachy):
    """
    Smaller interaction gesture:
    - Raises arm a little
    - Opens hand
    - Returns home
    """

    print("\n=== Small acknowledge gesture ===")

    current = safe_call(
        "Read right arm current positions",
        lambda: reachy.r_arm.get_current_positions()
    )

    if current is None:
        return

    home = current.copy()
    target = current.copy()

    target[0] = current[0] - 15
    target[1] = current[1] + 15
    target[3] = current[3] - 15

    safe_call(
        "Small raise right arm",
        lambda: reachy.r_arm.goto(target, duration=1.5, wait=True)
    )

    open_right_hand(reachy)
    time.sleep(1)

    safe_call(
        "Return right arm home",
        lambda: reachy.r_arm.goto(home, duration=1.5, wait=True)
    )


# =========================
# CAMERA + FACE INTERACTION
# =========================

def start_face_interaction(reachy):
    print("\nStarting face interaction mode.")
    print("Controls:")
    print("Q = quit")
    print("W = manual right arm wave")
    print("A = small acknowledge gesture")
    print("H = head center")
    print("S = safe/default posture")
    print("Keep E-stop nearby.\n")

    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    if face_cascade.empty():
        raise RuntimeError("OpenCV face detector could not be loaded.")

    last_head_move_time = 0
    last_wave_time = 0
    centered_start_time = None
    no_face_start_time = None

    while True:
        try:
            # Get camera frame from Reachy
            frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)

            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            frame_height, frame_width = frame_bgr.shape[:2]

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 60)
            )

            now = time.time()

            if len(faces) > 0:
                no_face_start_time = None

                # Pick largest face
                x, y, w, h = max(faces, key=lambda box: box[2] * box[3])

                face_center_x = x + w / 2
                face_center_y = y + h / 2

                cv2.rectangle(
                    frame_bgr,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.circle(
                    frame_bgr,
                    (int(face_center_x), int(face_center_y)),
                    5,
                    (255, 0, 0),
                    -1
                )

                if now - last_head_move_time > HEAD_MOVE_COOLDOWN:
                    status = move_head_to_track_face(
                        reachy,
                        face_center_x,
                        face_center_y,
                        frame_width,
                        frame_height
                    )

                    last_head_move_time = now
                    print("Face tracking status:", status)

                    if status == "centered":
                        if centered_start_time is None:
                            centered_start_time = now

                        centered_duration = now - centered_start_time

                        # Trigger greeting if face stays centered
                        if (
                            ENABLE_ARM_GESTURE
                            and centered_duration >= FACE_CENTER_SECONDS_TO_WAVE
                            and now - last_wave_time >= WAVE_COOLDOWN
                        ):
                            right_arm_greeting_wave(reachy)
                            last_wave_time = now
                            centered_start_time = None
                    else:
                        centered_start_time = None

                cv2.putText(
                    frame_bgr,
                    "Face detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

            else:
                centered_start_time = None

                if no_face_start_time is None:
                    no_face_start_time = now

                no_face_duration = now - no_face_start_time

                # If no face for a while, slowly center head
                if no_face_duration > 3 and now - last_head_move_time > 2:
                    print("No face detected for 3 seconds. Centering head.")
                    center_head(reachy)
                    last_head_move_time = now

                cv2.putText(
                    frame_bgr,
                    "No face detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

            cv2.imshow("Reachy Human Interaction", frame_bgr)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Quitting interaction.")
                break

            elif key == ord("w"):
                right_arm_greeting_wave(reachy)

            elif key == ord("a"):
                right_arm_small_acknowledge(reachy)

            elif key == ord("h"):
                center_head(reachy)

            elif key == ord("s"):
                go_safe_posture(reachy)

        except KeyboardInterrupt:
            print("Stopped by user.")
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(1)

    cv2.destroyAllWindows()

    print("Returning head to center...")
    center_head(reachy)
    print("Interaction stopped.")


# =========================
# MAIN
# =========================

def main():
    reachy = connect_reachy()

    print("\nRobot connected.")
    print("Head:", reachy.head)
    print("Right arm:", reachy.r_arm)
    print("Left arm:", reachy.l_arm)
    print("Cameras:", reachy.cameras)

    print("""
=================================
 Reachy Human Interaction Demo
=================================

This demo uses:
- Reachy camera for face detection
- Reachy head for face tracking
- Right arm for greeting wave
- Right hand/gripper if available

Safety:
- Keep E-stop nearby.
- Make sure right arm has free space.
- Mobile base is not used.

Options:
1 - Start face interaction
2 - Manual right arm greeting wave
3 - Small acknowledge gesture
4 - Center head
5 - Default/safe posture
q - Quit
""")

    while True:
        choice = input("Choose option: ").strip().lower()

        if choice == "1":
            start_face_interaction(reachy)

        elif choice == "2":
            right_arm_greeting_wave(reachy)

        elif choice == "3":
            right_arm_small_acknowledge(reachy)

        elif choice == "4":
            center_head(reachy)

        elif choice == "5":
            go_safe_posture(reachy)

        elif choice == "q":
            print("Exiting.")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()