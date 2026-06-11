from reachy2_sdk import ReachySDK
from reachy2_sdk.media.camera import CameraView

import cv2
import numpy as np
import time
import grpc

ROBOT_HOST = "10.116.19.109"

# Choose one color first.
# This example is for RED ball.
LOWER_COLOR_1 = np.array([0, 100, 80])
UPPER_COLOR_1 = np.array([10, 255, 255])

LOWER_COLOR_2 = np.array([170, 100, 80])
UPPER_COLOR_2 = np.array([180, 255, 255])


def safe_get_frame(reachy):
    try:
        frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)
        return frame
    except grpc.RpcError as e:
        print("Camera error:", e.code())
        return None
    except Exception as e:
        print("Camera error:", e)
        return None


def detect_red_ball(frame_bgr):
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, LOWER_COLOR_1, UPPER_COLOR_1)
    mask2 = cv2.inRange(hsv, LOWER_COLOR_2, UPPER_COLOR_2)
    mask = mask1 + mask2

    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None, mask

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    if area < 300:
        return None, mask

    (x, y), radius = cv2.minEnclosingCircle(largest)

    return {
        "x": int(x),
        "y": int(y),
        "radius": int(radius),
        "area": area,
    }, mask


def main():
    reachy = ReachySDK(host=ROBOT_HOST)

    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        raise RuntimeError("Cannot connect to Reachy.")

    reachy.turn_on()

    print("Color ball detection only.")
    print("This does NOT move the robot.")
    print("Press Q to quit.")

    while True:
        frame = safe_get_frame(reachy)

        if frame is None:
            time.sleep(1)
            continue

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        ball, mask = detect_red_ball(frame_bgr)

        if ball:
            cv2.circle(
                frame_bgr,
                (ball["x"], ball["y"]),
                ball["radius"],
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame_bgr,
                f"RED BALL x={ball['x']} y={ball['y']} area={int(ball['area'])}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            print("Ball detected:", ball)

        else:
            cv2.putText(
                frame_bgr,
                "No red ball",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        cv2.imshow("Reachy Color Ball Detection", frame_bgr)
        cv2.imshow("Color Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
    print("Stopped.")


if __name__ == "__main__":
    main()