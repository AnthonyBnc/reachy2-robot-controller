# vision_paper.py

import cv2
import numpy as np

from config import MIN_PAPER_AREA


def detect_paper(frame):
    """
    Detect a white paper-like rectangle from the camera frame.
    """

    if frame is None:
        return None

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # White paper threshold
    lower_white = np.array([0, 0, 145])
    upper_white = np.array([180, 90, 255])

    mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < MIN_PAPER_AREA:
            continue

        rect = cv2.minAreaRect(contour)
        (cx, cy), (rw, rh), angle = rect

        if rw <= 0 or rh <= 0:
            continue

        aspect_ratio = max(rw, rh) / min(rw, rh)

        # Paper-like rectangle ratio
        if 1.1 <= aspect_ratio <= 2.8:
            candidates.append({
                "center": (int(cx), int(cy)),
                "size": (int(rw), int(rh)),
                "angle": float(angle),
                "area": float(area),
                "rect": rect
            })

    if not candidates:
        return None

    return max(candidates, key=lambda item: item["area"])


def get_pickup_zone(frame):
    """
    Define the safe pickup zone in the camera image.
    Paper must be inside this zone before Reachy moves.
    """

    h, w = frame.shape[:2]

    x_min = int(w * 0.32)
    x_max = int(w * 0.68)
    y_min = int(h * 0.38)
    y_max = int(h * 0.82)

    return x_min, y_min, x_max, y_max


def is_inside_pickup_zone(paper, frame):
    """
    Check if detected paper center is inside pickup zone.
    """

    if paper is None:
        return False

    cx, cy = paper["center"]
    x_min, y_min, x_max, y_max = get_pickup_zone(frame)

    return x_min <= cx <= x_max and y_min <= cy <= y_max


def draw_debug(frame, paper, stable_count, required_stable_frames):
    """
    Draw pickup zone and detected paper.
    """

    debug = frame.copy()

    x_min, y_min, x_max, y_max = get_pickup_zone(debug)

    # Pickup zone
    cv2.rectangle(
        debug,
        (x_min, y_min),
        (x_max, y_max),
        (255, 0, 0),
        2
    )

    cv2.putText(
        debug,
        "Pickup Zone",
        (x_min, y_min - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 0),
        2
    )

    if paper is not None:
        box = cv2.boxPoints(paper["rect"])
        box = box.astype(int)

        cv2.drawContours(
            debug,
            [box],
            0,
            (0, 255, 0),
            2
        )

        cx, cy = paper["center"]

        cv2.circle(
            debug,
            (cx, cy),
            6,
            (0, 0, 255),
            -1
        )

        cv2.putText(
            debug,
            "Paper detected",
            (cx + 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    cv2.putText(
        debug,
        f"Stable: {stable_count}/{required_stable_frames}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        debug,
        "G = force grasp | Q = quit",
        (20, debug.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    return debug