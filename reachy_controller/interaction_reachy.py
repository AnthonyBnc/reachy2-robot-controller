from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView

import pyttsx3
import cv2
import time
import threading


ROBOT_HOST = "10.116.19.109"

reachy = ReachySDK(host=ROBOT_HOST)

print("Connected:", reachy.is_connected())

if not reachy.is_connected():
    raise Exception("Cannot connect to Reachy")

reachy.turn_on()


# -----------------------------
# Text-to-speech setup
# -----------------------------

speaker = pyttsx3.init()
speaker.setProperty("rate", 160)
speaker.setProperty("volume", 1.0)


def say(text):
    print("Reachy says:", text)
    speaker.say(text)
    speaker.runAndWait()


def say_async(text):
    """
    Speak while Reachy is moving.
    This prevents the robot from waiting until the speech is finished.
    """
    thread = threading.Thread(target=say, args=(text,))
    thread.daemon = True
    thread.start()


# -----------------------------
# OpenCV face detector
# -----------------------------

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# -----------------------------
# Timing / detection settings
# -----------------------------

last_wave_time = 0
last_head_move_time = 0
face_ready_count = 0

# Farther face detection settings
MIN_FACE_SIZE = (40, 40)      # smaller = detect farther faces
SCALE_FACTOR = 1.1            # smaller = more sensitive
MIN_NEIGHBORS = 4             # lower = more sensitive, but more false positives

# Action trigger settings
FACE_STABLE_FRAMES = 5        # face must stay valid for several frames
WAVE_COOLDOWN = 12            # seconds between waves

# Face distance filter based on detected face area in pixels.
# If face is smaller than MIN_FACE_AREA_FOR_WAVE, person is too far.
# If face is larger than MAX_FACE_AREA_FOR_WAVE, person is too close.
MIN_FACE_AREA_FOR_WAVE = 1600     # about 40x40
MAX_FACE_AREA_FOR_WAVE = 70000    # reduce if it still triggers too close


# -----------------------------
# Head tracking helpers
# -----------------------------

def get_face_offset(face, frame_width, frame_height):
    x, y, w, h = face

    face_x = x + w / 2
    face_y = y + h / 2

    offset_x = (face_x - frame_width / 2) / (frame_width / 2)
    offset_y = (face_y - frame_height / 2) / (frame_height / 2)

    return offset_x, offset_y


def is_face_centered(face, frame_width, frame_height):
    offset_x, offset_y = get_face_offset(face, frame_width, frame_height)

    return abs(offset_x) < 0.18 and abs(offset_y) < 0.18


def look_at_face(face, frame_width, frame_height):
    offset_x, offset_y = get_face_offset(face, frame_width, frame_height)

    # If face is near center, do not move head
    if abs(offset_x) < 0.18 and abs(offset_y) < 0.18:
        return True

    # Small and slow head movement
    target_y = -0.18 * offset_x
    target_z = -0.12 * offset_y

    reachy.head.look_at(
        x=0.5,
        y=target_y,
        z=target_z,
        duration=1.2,
    )

    return False


def get_face_distance_status(face_area):
    """
    Estimate whether the person is too far, good distance, or too close
    based on detected face area in pixels.
    """
    if face_area < MIN_FACE_AREA_FOR_WAVE:
        return "too_far"

    if face_area > MAX_FACE_AREA_FOR_WAVE:
        return "too_close"

    return "good"


# -----------------------------
# Right hand wave
# Wrist roll kept.
# Gripper open/close removed.
# -----------------------------

def wave_right_hand():
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
    raised[3] = current[3] - 40   # elbow pitch, safer than -80

    # Keep wrist roll
    raised[4] = current[4] + 10   # wrist roll

    reachy.r_arm.goto(raised, duration=2.5, wait=True)

    wave_left = raised.copy()
    wave_right = raised.copy()

    # Wave left movement
    wave_left[2] = raised[2] + 10     # elbow yaw
    wave_left[3] = raised[3] - 10     # elbow pitch
    wave_left[4] = raised[4] + 20     # wrist roll
    wave_left[6] = raised[6] + 15     # wrist yaw

    # Wave right movement
    wave_right[2] = raised[2] - 10    # elbow yaw
    wave_right[3] = raised[3] - 10    # elbow pitch
    wave_right[4] = raised[4] - 20    # wrist roll
    wave_right[6] = raised[6] - 15    # wrist yaw

    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)

    # Return to raised pose first, then home
    reachy.r_arm.goto(raised, duration=1.0, wait=True)
    reachy.r_arm.goto(home, duration=2.5, wait=True)

    print("Wave complete.")


# -----------------------------
# Main face interaction loop
# -----------------------------

print("Starting simple face interaction.")
print("Press Q to quit.")
print("Keep E-stop nearby.")

while True:
    frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)

    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    # Improve contrast for farther face detection
    gray = cv2.equalizeHist(gray)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=SCALE_FACTOR,
        minNeighbors=MIN_NEIGHBORS,
        minSize=MIN_FACE_SIZE,
    )

    frame_height, frame_width = frame_bgr.shape[:2]

    if len(faces) > 0:
        # Choose biggest face only
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face

        face_area = w * h
        distance_status = get_face_distance_status(face_area)
        centered = is_face_centered(face, frame_width, frame_height)

        cv2.rectangle(
            frame_bgr,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame_bgr,
            f"Face size: {w}x{h}, area={face_area}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        now = time.time()

        # Move head slowly, not every frame
        if now - last_head_move_time > 1.0:
            look_at_face(face, frame_width, frame_height)
            last_head_move_time = now

        # Decide whether this face is allowed to trigger the wave
        if distance_status == "too_far":
            face_ready_count = 0
            status_text = "Face detected but too far"

        elif distance_status == "too_close":
            face_ready_count = 0
            status_text = "Face too close - action blocked"

        else:
            status_text = "Good distance"

            if centered:
                face_ready_count += 1
            else:
                face_ready_count = 0

        cv2.putText(
            frame_bgr,
            status_text,
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        cv2.putText(
            frame_bgr,
            f"Centered: {centered}",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        cv2.putText(
            frame_bgr,
            f"Stable frames: {face_ready_count}/{FACE_STABLE_FRAMES}",
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        # Trigger wave only when:
        # 1. Face is at a good distance
        # 2. Face is centered
        # 3. Face is stable for several frames
        # 4. Cooldown has passed
        if (
            distance_status == "good"
            and centered
            and face_ready_count >= FACE_STABLE_FRAMES
            and now - last_wave_time > WAVE_COOLDOWN
        ):
            wave_right_hand()
            last_wave_time = time.time()
            face_ready_count = 0

        cv2.putText(
            frame_bgr,
            "Face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    else:
        face_ready_count = 0

        cv2.putText(
            frame_bgr,
            "No face",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )

    cv2.imshow("Reachy Simple Face Interaction", frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()

# Return head to center when finished
reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)

print("Stopped.")