import time
from pathlib import Path

from config import ROBOT_HOST


CAMERA_RETRY_DELAY = 1.0
CAMERA_MAX_RETRIES = 5


def connect_reachy_for_camera(host=ROBOT_HOST):
    try:
        from reachy2_sdk import ReachySDK
    except ImportError as e:
        raise RuntimeError(
            "Reachy SDK is not installed. Run: python -m pip install reachy2-sdk==1.0.7 reachy2-sdk-api==1.0.11"
        ) from e

    reachy = ReachySDK(host=host)
    print("Reachy connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise ConnectionError(f"Cannot connect to Reachy at {host}. Check IP, network, and SDK server.")

    print("Available cameras:")
    print(reachy.cameras)

    return reachy


def get_camera_view(view_name):
    from reachy2_sdk.media.camera import CameraView

    views = {
        "left": CameraView.LEFT,
        "right": CameraView.RIGHT,
    }

    normalized_view = view_name.lower().strip()

    if normalized_view not in views:
        raise ValueError("Camera view must be 'left' or 'right'.")

    return views[normalized_view]


def get_teleop_frame(reachy, view_name="left", max_retries=CAMERA_MAX_RETRIES, delay=CAMERA_RETRY_DELAY):
    view = get_camera_view(view_name)

    for attempt in range(1, max_retries + 1):
        try:
            frame, timestamp = reachy.cameras.teleop.get_frame(view)
            return frame, timestamp

        except Exception as e:
            print(f"Camera frame error, retry {attempt}/{max_retries}: {e}")

            if attempt == max_retries:
                raise

            time.sleep(delay)

    return None, None


def save_frame(frame, output_path):
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("Pillow is not installed. Run: python -m pip install pillow") from e

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    Image.fromarray(frame).save(output_path)
    return output_path


def capture_teleop_frame(host=ROBOT_HOST, view_name="left", output_path=None):
    reachy = connect_reachy_for_camera(host)
    frame, timestamp = get_teleop_frame(reachy, view_name=view_name)

    if output_path is None:
        output_path = Path("reachy_full_demo/camera/output") / f"teleop_{view_name}.png"

    saved_path = save_frame(frame, output_path)

    print("[OK] Camera frame captured")
    print("Saved to:", saved_path)
    print("Timestamp:", timestamp)

    return saved_path, timestamp


def show_teleop_camera(host=ROBOT_HOST, view_name="left"):
    try:
        import cv2
    except ImportError as e:
        raise RuntimeError("OpenCV is not installed. Run: python -m pip install opencv-python") from e

    reachy = connect_reachy_for_camera(host)

    print("Starting Reachy teleop camera viewer.")
    print("Press Q to quit.")

    while True:
        try:
            frame, timestamp = get_teleop_frame(reachy, view_name=view_name)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            cv2.imshow(f"Reachy Teleop Camera - {view_name}", frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        except KeyboardInterrupt:
            break

        except Exception as e:
            print("Camera viewer error:", e)
            time.sleep(CAMERA_RETRY_DELAY)

    cv2.destroyAllWindows()
