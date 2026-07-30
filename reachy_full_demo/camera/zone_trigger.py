import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from camera.camera_access import connect_reachy_for_camera, get_teleop_frame
from config import ROBOT_HOST


@dataclass(frozen=True)
class TriggerZone:
    name: str
    x1_ratio: float
    y1_ratio: float
    x2_ratio: float
    y2_ratio: float

    def to_pixels(self, frame_width, frame_height):
        return (
            int(self.x1_ratio * frame_width),
            int(self.y1_ratio * frame_height),
            int(self.x2_ratio * frame_width),
            int(self.y2_ratio * frame_height),
        )


# Tune these two boxes after looking at the live camera.
# Coordinates are ratios of the image: x1, y1, x2, y2.
DEFAULT_ZONES = [
    TriggerZone("left_point", 0.18, 0.25, 0.42, 0.88),
    TriggerZone("right_point", 0.58, 0.25, 0.82, 0.88),
]


def box_center(box):
    x, y, w, h = box
    return x + w / 2, y + h / 2


def point_in_zone(point, zone_pixels):
    x, y = point
    x1, y1, x2, y2 = zone_pixels
    return x1 <= x <= x2 and y1 <= y <= y2


def face_area(face):
    return face[2] * face[3]


def create_face_detector():
    import cv2

    return cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )


def find_faces(frame_bgr, detector):
    import cv2

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    return detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(40, 40),
    )


def draw_zones(frame_bgr, zones, active_zone_name=None):
    import cv2

    frame_height, frame_width = frame_bgr.shape[:2]

    for zone in zones:
        x1, y1, x2, y2 = zone.to_pixels(frame_width, frame_height)
        color = (0, 220, 255)

        if zone.name == active_zone_name:
            color = (0, 255, 0)

        cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame_bgr,
            zone.name,
            (x1, max(24, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )


def draw_faces(frame_bgr, faces, zone_hits):
    import cv2

    for face in faces:
        x, y, w, h = face
        center = box_center(face)
        hit_zone = zone_hits.get(tuple(face))
        color = (0, 255, 0) if hit_zone else (255, 160, 0)

        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), color, 2)
        cv2.circle(frame_bgr, (int(center[0]), int(center[1])), 5, color, -1)

        if hit_zone:
            cv2.putText(
                frame_bgr,
                f"in {hit_zone}",
                (x, y + h + 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
            )


def get_active_zone(faces, zones, frame_width, frame_height, min_face_area):
    biggest_hit = None
    biggest_area = 0
    zone_hits = {}

    for face in faces:
        area = face_area(face)

        if area < min_face_area:
            continue

        center = box_center(face)

        for zone in zones:
            if point_in_zone(center, zone.to_pixels(frame_width, frame_height)):
                zone_hits[tuple(face)] = zone.name

                if area > biggest_area:
                    biggest_area = area
                    biggest_hit = zone.name

                break

    return biggest_hit, zone_hits


def run_full_demo_once(reachy):
    from ai.ai_brain import create_ai_client
    from main import run_one_demo_cycle

    client = create_ai_client()
    run_one_demo_cycle(client, reachy, cycle_number=1)


def monitor_trigger_zones(
    host=ROBOT_HOST,
    view_name="left",
    zones=None,
    stable_frames_required=8,
    cooldown_seconds=45,
    min_face_area=1600,
    run_workflow=False,
):
    import cv2

    zones = zones or DEFAULT_ZONES
    reachy = connect_reachy_for_camera(host)

    stable_zone = None
    stable_count = 0
    last_trigger_time = 0
    face_detector = create_face_detector()

    print("Starting fixed-zone audience trigger.")
    print("Press Q to quit.")
    print("Yellow boxes are trigger points. Green means a stable hit is forming.")

    while True:
        frame, timestamp = get_teleop_frame(reachy, view_name=view_name)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_height, frame_width = frame_bgr.shape[:2]

        faces = find_faces(frame_bgr, face_detector)
        active_zone, zone_hits = get_active_zone(
            faces,
            zones,
            frame_width,
            frame_height,
            min_face_area,
        )

        if active_zone is None:
            stable_zone = None
            stable_count = 0
        elif active_zone == stable_zone:
            stable_count += 1
        else:
            stable_zone = active_zone
            stable_count = 1

        now = time.time()
        ready = (
            stable_zone is not None
            and stable_count >= stable_frames_required
            and now - last_trigger_time >= cooldown_seconds
        )

        draw_zones(frame_bgr, zones, active_zone_name=stable_zone)
        draw_faces(frame_bgr, faces, zone_hits)

        status = "Waiting for audience in trigger zone"
        if stable_zone:
            status = f"{stable_zone}: {stable_count}/{stable_frames_required}"
        if now - last_trigger_time < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_trigger_time))
            status = f"Cooldown: {remaining}s"

        cv2.putText(
            frame_bgr,
            status,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        if ready:
            print(f"[TRIGGER] Audience detected in {stable_zone}")
            last_trigger_time = now
            stable_count = 0

            if run_workflow:
                cv2.destroyAllWindows()
                run_full_demo_once(reachy)
                print("Workflow complete. Returning to zone monitor.")

        cv2.imshow("Reachy Audience Trigger Zones", frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Trigger the Reachy workflow from fixed audience zones.")
    parser.add_argument("--host", default=ROBOT_HOST, help="Reachy IP address.")
    parser.add_argument("--view", choices=["left", "right"], default="left")
    parser.add_argument("--stable-frames", type=int, default=8)
    parser.add_argument("--cooldown", type=float, default=45)
    parser.add_argument("--min-face-area", type=int, default=1600)
    parser.add_argument(
        "--run-workflow",
        action="store_true",
        help="Run one full demo cycle when a zone is triggered.",
    )
    args = parser.parse_args()

    try:
        monitor_trigger_zones(
            host=args.host,
            view_name=args.view,
            stable_frames_required=args.stable_frames,
            cooldown_seconds=args.cooldown,
            min_face_area=args.min_face_area,
            run_workflow=args.run_workflow,
        )
    except Exception as e:
        print("[FAILED] Zone trigger monitor")
        print("Error:", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
