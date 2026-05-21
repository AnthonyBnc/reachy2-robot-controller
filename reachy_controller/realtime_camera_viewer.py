from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView
import cv2
import time

ROBOT_HOST = "YOUR_IP"  # change if Reachy's IP changes


def connect_reachy():
    reachy = ReachySDK(host=ROBOT_HOST)
    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise ConnectionError("Cannot connect to Reachy.")

    print("Available cameras:")
    print(reachy.cameras)

    return reachy


def show_teleop_camera(reachy, view=CameraView.LEFT):
    print("Starting real-time camera viewer...")
    print("Press Q to quit.")

    while True:
        try:
            frame, timestamp = reachy.cameras.teleop.get_frame(view)

            # Convert BGR/RGB if needed
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            cv2.imshow("Reachy Teleop Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        except KeyboardInterrupt:
            break

        except Exception as e:
            print("Camera error:", e)
            time.sleep(1)

    cv2.destroyAllWindows()


def main():
    reachy = connect_reachy()

    print("""
Choose camera:
1 - Teleop LEFT camera
2 - Teleop RIGHT camera
""")

    choice = input("Choose option: ").strip()

    if choice == "1":
        show_teleop_camera(reachy, CameraView.LEFT)

    elif choice == "2":
        show_teleop_camera(reachy, CameraView.RIGHT)

    else:
        print("Invalid option.")


if __name__ == "__main__":
    main()