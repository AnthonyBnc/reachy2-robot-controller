from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView

import cv2
import time
import threading
import subprocess
import grpc


# =========================
# CONFIG
# =========================

ROBOT_HOST = "10.116.19.109"

# macOS system voice
# To list available voices in Terminal:
# say -v ?
MACOS_VOICE = "Samantha"
SPEECH_RATE = "160"

# Safety switch
# Set this to False if you only want face tracking + speaking.
# Set this to True only when the right arm has clear space.
ENABLE_ARM_WAVE = True

# Face logic
FACE_MIN_SIZE = (70, 70)
HEAD_MOVE_COOLDOWN = 1.0
WAVE_COOLDOWN = 12.0

# Camera retry logic
CAMERA_MAX_RETRIES = 5
CAMERA_RETRY_DELAY = 1.0


# =========================
# CONNECT TO REACHY
# =========================

reachy = ReachySDK(host=ROBOT_HOST)

print("Connected:", reachy.is_connected())

if not reachy.is_connected():
    raise Exception("Cannot connect to Reachy")

reachy.turn_on()


# =========================
# MACOS SPEAKER
# =========================

def say(text):
    """
    Speak through macOS system speaker.

    This replaces pyttsx3 because pyttsx3 can crash on macOS
    due to NSSpeech / PyObjC driver issues.
    """
    print("Reachy says:", text)

    try:
        subprocess.run([
            "say",
            "-v", MACOS_VOICE,
            "-r", SPEECH_RATE,
            text
        ])
    except Exception as e:
        print("Speech error:", e)


def say_async(text):
    """
    Speak while Reachy is moving.
    This prevents the robot movement from waiting for speech to finish.
    """
    thread = threading.Thread(target=say, args=(text,))
    thread.daemon = True
    thread.start()


# =========================
# CAMERA SAFE WRAPPER
# =========================

def safe_get_camera_frame(max_retries=CAMERA_MAX_RETRIES, delay=CAMERA_RETRY_DELAY):
    """
    Safely get one camera frame from Reachy.

    If the camera stream temporarily breaks with:
    - Broken pipe
    - gRPC UNAVAILABLE

    then retry instead of crashing the whole script.
    """

    for attempt in range(max_retries):
        try:
            frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)
            return frame, timestamp

        except grpc.RpcError as e:
            print(f"Camera frame error, retry {attempt + 1}/{max_retries}: {e.code()}")

            if e.code() == grpc.StatusCode.UNAVAILABLE:
                time.sleep(delay)
                continue

            raise e

        except Exception as e:
            print(f"Unexpected camera error, retry {attempt + 1}/{max_retries}: {e}")
            time.sleep(delay)

    return None, None


# =========================
# FACE DETECTOR
# =========================

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

if face_detector.empty():
    raise RuntimeError("Could not load OpenCV Haar cascade face detector.")


# =========================
# HEAD TRACKING
# =========================

def look_at_face(face, frame_width, frame_height):
    x, y, w, h = face

    face_x = x + w / 2
    face_y = y + h / 2

    # Offset from screen center
    offset_x = (face_x - frame_width / 2) / (frame_width / 2)
    offset_y = (face_y - frame_height / 2) / (frame_height / 2)

    # If face is near center, do not move head
    if abs(offset_x) < 0.18 and abs(offset_y) < 0.18:
        return True

    # Small and slow head movement
    target_y = -0.18 * offset_x
    target_z = -0.12 * offset_y

    # Extra clamp for safety
    target_y = max(-0.25, min(0.25, target_y))
    target_z = max(-0.15, min(0.20, target_z))

    reachy.head.look_at(
        x=0.5,
        y=target_y,
        z=target_z,
        duration=1.2
    )

    return False


# =========================
# ARM GESTURE
# =========================

def wave_right_hand():
    """
    Right hand wave gesture.

    IMPORTANT:
    This uses your previous best working version.
    If the arm moves too close to the robot body, stop the script
    and set ENABLE_ARM_WAVE = False.
    """

    if not ENABLE_ARM_WAVE:
        print("Arm wave is disabled. Speaking only.")
        say_async("Hello, I am Reachy. Nice to meet you.")
        return

    print("Waving...")

    # Voice starts at the same time as the waving gesture
    say_async("Hello, I am Reachy. Nice to meet you.")

    current = reachy.r_arm.get_current_positions()
    home = current.copy()

    raised = current.copy()

    # Joint order:
    # 0 = shoulder pitch
    # 1 = shoulder roll
    # 2 = elbow yaw
    # 3 = elbow pitch
    # 4 = wrist roll
    # 5 = wrist pitch
    # 6 = wrist yaw

    raised[0] = current[0] - 15   # shoulder pitch
    raised[1] = current[1] + 18   # shoulder roll
    raised[2] = current[2] + 8    # elbow yaw
    raised[3] = current[3] - 25   # elbow pitch

    reachy.r_arm.goto(raised, duration=2.5, wait=True)

    try:
        reachy.r_arm.gripper.set_opening(100)
    except Exception as e:
        print("Right gripper not available:", e)

    wave_left = raised.copy()
    wave_right = raised.copy()

    # Elbow + wrist movement while waving
    wave_left[2] = raised[2] + 10
    wave_left[3] = raised[3] - 15
    wave_left[6] = raised[6] + 15

    wave_right[2] = raised[2] - 10
    wave_right[3] = raised[3] - 15
    wave_right[6] = raised[6] - 15

    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)

    # Return to raised pose first, then home
    reachy.r_arm.goto(raised, duration=1.0, wait=True)
    reachy.r_arm.goto(home, duration=2.5, wait=True)

    print("Wave finished.")


# =========================
# MAIN LOOP
# =========================

last_wave_time = 0
last_head_move_time = 0

print("Starting simple face interaction.")
print("Press Q to quit.")
print("Keep E-stop nearby.")
print("Using macOS system speaker.")
print("Arm wave enabled:", ENABLE_ARM_WAVE)

try:
    while True:
        frame, timestamp = safe_get_camera_frame()

        if frame is None:
            print("Camera unavailable. Skipping this frame.")
            time.sleep(0.5)
            continue

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=FACE_MIN_SIZE
        )

        frame_height, frame_width = frame_bgr.shape[:2]

        if len(faces) > 0:
            # Choose biggest face only
            face = max(faces, key=lambda f: f[2] * f[3])

            x, y, w, h = face
            face_area = w * h

            cv2.rectangle(
                frame_bgr,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame_bgr,
                f"Face detected | area: {face_area}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            now = time.time()

            # Move head slowly, not every frame
            if now - last_head_move_time > HEAD_MOVE_COOLDOWN:
                centered = look_at_face(face, frame_width, frame_height)
                last_head_move_time = now

                # If face is centered, greet only once every 12 seconds
                if centered and now - last_wave_time > WAVE_COOLDOWN:
                    wave_right_hand()
                    last_wave_time = time.time()

        else:
            cv2.putText(
                frame_bgr,
                "No face",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        cv2.imshow("Reachy Simple Face Interaction - macOS", frame_bgr)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Q pressed. Exiting.")
            break

except KeyboardInterrupt:
    print("Keyboard interrupt received. Stopping.")

except Exception as e:
    print("Unexpected error:", e)

finally:
    print("Cleaning up...")

    cv2.destroyAllWindows()

    try:
        reachy.head.look_at(
            x=0.5,
            y=0.0,
            z=0.0,
            duration=1.5
        )
    except Exception as e:
        print("Could not return head to center:", e)

    print("Stopped.")