import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import ROBOT_HOST
from camera.camera_access import capture_teleop_frame, show_teleop_camera


def main():
    parser = argparse.ArgumentParser(description="Access Reachy's teleop camera.")
    parser.add_argument("--host", default=ROBOT_HOST, help="Reachy IP address.")
    parser.add_argument(
        "--view",
        choices=["left", "right"],
        default="left",
        help="Teleop camera view to use.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Open a live OpenCV camera window instead of capturing one frame.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output image path for one-frame capture.",
    )
    args = parser.parse_args()

    try:
        if args.live:
            show_teleop_camera(host=args.host, view_name=args.view)
        else:
            capture_teleop_frame(
                host=args.host,
                view_name=args.view,
                output_path=args.output,
            )
    except Exception as e:
        print("[FAILED] Reachy camera access")
        print("Error:", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
