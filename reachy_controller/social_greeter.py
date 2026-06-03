from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView
import cv2
import time
import pyttsx3
import threading

ROBOT_HOST = "10.116.19.109"

# Connect to Reachy
reachy = ReachySDK(host=ROBOT_HOST)
print("Connected:", reachy.is_connected())

if not reachy.is_connected():
    raise Exception("Cannot connect to Reachy")

reachy.turn_on()

# Speaker setup
speaker = pyttsx3.init()
speaker.setProperty("rate", 160)
speaker.setProperty("volume", 1.0)


def say(text):
    print("Reachy says:", text)
    speaker.say(text)
    speaker.runAndWait()


def say_async(text):
    threading.Thread(target=say, args=(text,), daemon=True).start()


# Face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

last_wave_time = 0
last_head_move_time = 0
last_scan_time = 0
scan_position = 0


def center_head():
    reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)


def scan_head():
    global scan_position

    if scan_position == 0:
        reachy.head.look_at(x=0.5, y=0.18, z=0.0, duration=2.0)
        print("Scanning left")

    elif scan_position == 1:
        reachy.head.look_at(x=0.5, y=-0.18, z=0.0, duration=2.0)
        print("Scanning right")

    else:
        center_head()
        print("Scanning center")

    scan_position = (scan_position + 1) % 3


def look_at_face(face, frame_width, frame_height):
    x, y, w, h = face

    face_x = x + w / 2
    face_y = y + h / 2

    offset_x = (face_x - frame_width / 2) / (frame_width / 2)
    offset_y = (face_y - frame_height / 2) / (frame_height / 2)

    # Face is already near center
    if abs(offset_x) < 0.18 and abs(offset_y) < 0.18:
        return True

    target_y = -0.18 * offset_x
    target_z = -0.12 * offset_y

    reachy.head.look_at(
        x=0.5,
        y=target_y,
        z=target_z,
        duration=1.2
    )

    return False


def wave_right_hand():
    say_async("Hello, I am Reachy. Nice to meet you.")

    current = reachy.r_arm.get_current_positions()
    home = current.copy()

    # Joint order:
    # 0 shoulder pitch
    # 1 shoulder roll
    # 2 elbow yaw
    # 3 elbow pitch
    # 6 wrist yaw

    raised = current.copy()
    raised[0] = current[0] - 15
    raised[1] = current[1] + 18
    raised[2] = current[2] + 8
    raised[3] = current[3] - 25

    reachy.r_arm.goto(raised, duration=2.5, wait=True)

    try:
        reachy.r_arm.gripper.set_opening(100)
    except Exception:
        pass

    wave_left = raised.copy()
    wave_right = raised.copy()

    wave_left[2] = raised[2] + 10
    wave_left[3] = raised[3] - 12
    wave_left[6] = raised[6] + 15

    wave_right[2] = raised[2] - 10
    wave_right[3] = raised[3] - 12
    wave_right[6] = raised[6] - 15

    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_right, duration=1.0, wait=True)
    reachy.r_arm.goto(wave_left, duration=1.0, wait=True)

    reachy.r_arm.goto(raised, duration=1.0, wait=True)
    reachy.r_arm.goto(home, duration=2.5, wait=True)


print("Starting simple social greeter.")
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
        minSize=(70, 70)
    )

    frame_height, frame_width = frame_bgr.shape[:2]
    now = time.time()

    if len(faces) > 0:
        # Choose biggest face only
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face

        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if now - last_head_move_time > 1.0:
            centered = look_at_face(face, frame_width, frame_height)
            last_head_move_time = now

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
            2
        )

    else:
        if now - last_scan_time > 3.0:
            scan_head()
            last_scan_time = now

        cv2.putText(
            frame_bgr,
            "No face - scanning",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    cv2.imshow("Reachy Simple Social Greeter", frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
center_head()

print("Stopped.")