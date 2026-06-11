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

last_wave_time = 0
last_head_move_time = 0


# -----------------------------
# Head tracking
# -----------------------------

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

    reachy.head.look_at(
        x=0.5,
        y=target_y,
        z=target_z,
        duration=1.2,
    )

    return False


# -----------------------------
# Right hand wave with wrist roll
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

    # Safer than -80. If you already tested -80 safely, you can change this back.
    raised[3] = current[3] - 40   # elbow pitch

    # NEW: wrist roll setup before waving
    raised[4] = current[4] + 10   # wrist roll

    reachy.r_arm.goto(raised, duration=2.5, wait=True)

    try:
        reachy.r_arm.gripper.set_opening(100)
    except Exception as e:
        print("Could not open gripper:", e)

    wave_left = raised.copy()
    wave_right = raised.copy()

    # Wave left movement
    wave_left[2] = raised[2] + 10     # elbow yaw
    wave_left[3] = raised[3] - 10     # elbow pitch
    wave_left[4] = raised[4] + 20     # NEW: wrist roll
    wave_left[6] = raised[6] + 15     # wrist yaw

    # Wave right movement
    wave_right[2] = raised[2] - 10    # elbow yaw
    wave_right[3] = raised[3] - 10    # elbow pitch
    wave_right[4] = raised[4] - 20    # NEW: wrist roll
    wave_right[6] = raised[6] - 15    # wrist yaw

    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)

    # Return to raised pose first
    reachy.r_arm.goto(raised, duration=1.0, wait=True)

    # Relax hand
    try:
        reachy.r_arm.gripper.set_opening(60)
    except Exception as e:
        print("Could not relax gripper:", e)

    # Return to home pose
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

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(70, 70),
    )

    frame_height, frame_width = frame_bgr.shape[:2]

    if len(faces) > 0:
        # Choose biggest face only
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face

        cv2.rectangle(
            frame_bgr,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2,
        )

        now = time.time()

        # Move head slowly, not every frame
        if now - last_head_move_time > 1.0:
            centered = look_at_face(face, frame_width, frame_height)
            last_head_move_time = now

            # If face is centered, wave only once every 12 seconds
            if centered and now - last_wave_time > 12:
                wave_right_hand()
                last_wave_time = time.time()

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