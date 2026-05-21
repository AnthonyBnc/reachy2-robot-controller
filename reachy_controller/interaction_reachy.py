from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView
import cv2
import time

ROBOT_HOST = "YOUR_IP"  # change if Reachy's IP changes

# Safety settings
ENABLE_ARM_WAVE = True
HEAD_MOVE_COOLDOWN = 0.6
WAVE_COOLDOWN = 8.0


def connect_reachy():
    reachy = ReachySDK(host=ROBOT_HOST)
    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise ConnectionError("Cannot connect to Reachy.")

    reachy.turn_on()
    return reachy


def move_head_based_on_face(reachy, face_center_x, face_center_y, frame_width, frame_height):
    """
    Move Reachy's head based on where the face is in the camera frame.
    This is simple rule-based tracking.
    """

    # Convert face position into offset from center
    offset_x = (face_center_x - frame_width / 2) / (frame_width / 2)
    offset_y = (face_center_y - frame_height / 2) / (frame_height / 2)

    # Dead zone: if face is near center, do not move
    if abs(offset_x) < 0.15 and abs(offset_y) < 0.15:
        return "centered"

    # Reachy look_at coordinates
    # y positive/negative changes left-right
    # z positive/negative changes up-down
    y = -0.25 * offset_x
    z = -0.20 * offset_y

    # Limit movement
    y = max(-0.25, min(0.25, y))
    z = max(-0.15, min(0.20, z))

    reachy.head.look_at(x=0.5, y=y, z=z, duration=0.5)

    if offset_x > 0.15:
        return "face right"
    elif offset_x < -0.15:
        return "face left"
    elif offset_y > 0.15:
        return "face down"
    elif offset_y < -0.15:
        return "face up"

    return "tracking"


def wave_right_arm(reachy):
    """
    Very small safe wave using current right arm position.
    It only changes the wrist yaw a little, then returns.
    """

    print("Waving right hand...")

    current = reachy.r_arm.get_current_positions()
    target_1 = current.copy()
    target_2 = current.copy()

    # Joint order:
    # shoulder pitch, shoulder roll, elbow yaw, elbow pitch,
    # wrist roll, wrist pitch, wrist yaw

    target_1[6] = current[6] + 15
    target_2[6] = current[6] - 15

    reachy.r_arm.goto(target_1, duration=0.7, wait=True)
    reachy.r_arm.goto(target_2, duration=0.7, wait=True)
    reachy.r_arm.goto(target_1, duration=0.7, wait=True)
    reachy.r_arm.goto(current, duration=1.0, wait=True)

    print("Wave done.")


def main():
    reachy = connect_reachy()

    print("Starting human interaction mode.")
    print("Press Q in the camera window to quit.")
    print("Keep E-stop nearby.")

    # OpenCV built-in face detector
    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    last_head_move_time = 0
    last_wave_time = 0
    centered_start_time = None

    while True:
        try:
            frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)

            # Convert for OpenCV display
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(60, 60)
            )

            frame_height, frame_width = frame_bgr.shape[:2]

            if len(faces) > 0:
                # Pick the largest face
                x, y, w, h = max(faces, key=lambda box: box[2] * box[3])

                face_center_x = x + w / 2
                face_center_y = y + h / 2

                cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)

                now = time.time()

                if now - last_head_move_time > HEAD_MOVE_COOLDOWN:
                    status = move_head_based_on_face(
                        reachy,
                        face_center_x,
                        face_center_y,
                        frame_width,
                        frame_height
                    )
                    last_head_move_time = now
                    print("Tracking status:", status)

                    if status == "centered":
                        if centered_start_time is None:
                            centered_start_time = now

                        centered_duration = now - centered_start_time

                        if (
                            ENABLE_ARM_WAVE
                            and centered_duration > 2.0
                            and now - last_wave_time > WAVE_COOLDOWN
                        ):
                            wave_right_arm(reachy)
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

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        except KeyboardInterrupt:
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(1)

    cv2.destroyAllWindows()

    print("Returning head to center...")
    try:
        reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)
    except Exception as e:
        print("Could not center head:", e)

    print("Stopped.")


if __name__ == "__main__":
    main()