from reachy2_sdk import ReachySDK
import time

ROBOT_HOST = "10.116.19.109" 


def print_section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def safe_check(name, func):
    try:
        result = func()
        print(f"[OK] {name}")
        if result is not None:
            print(result)
        return result
    except Exception as e:
        print(f"[FAILED] {name}")
        print("Error:", e)
        return None


def list_possible_attributes(reachy):
    print_section("Available top-level SDK attributes")

    attrs = [
        attr for attr in dir(reachy)
        if not attr.startswith("_")
    ]

    for attr in attrs:
        print("-", attr)


def check_basic_robot_parts(reachy):
    print_section("Robot parts access")

    safe_check("Head object", lambda: reachy.head)
    safe_check("Right arm object", lambda: reachy.r_arm)
    safe_check("Left arm object", lambda: reachy.l_arm)
    safe_check("Cameras object", lambda: reachy.cameras)

    if hasattr(reachy, "mobile_base"):
        safe_check("Mobile base object", lambda: reachy.mobile_base)
    else:
        print("[INFO] mobile_base attribute not found")

    # Check possible audio-related attributes
    possible_audio_attrs = [
        "microphone",
        "microphones",
        "mic",
        "audio",
        "speaker",
        "speakers",
        "sound",
    ]

    print_section("Possible mic / speaker attributes")

    found_audio = False
    for attr in possible_audio_attrs:
        if hasattr(reachy, attr):
            found_audio = True
            safe_check(attr, lambda attr=attr: getattr(reachy, attr))

    if not found_audio:
        print("[INFO] No obvious mic/speaker attribute found in this SDK object.")
        print("[INFO] This does not mean the robot has no mic/speaker; it may not be exposed through this SDK version.")


def check_motor_read_access(reachy):
    print_section("Motor / joint read access")

    safe_check("Head status", lambda: reachy.head)
    safe_check("Right arm positions", lambda: reachy.r_arm.get_current_positions())
    safe_check("Left arm positions", lambda: reachy.l_arm.get_current_positions())


def check_small_head_control(reachy):
    print_section("Small head control test")

    answer = input("Run a small head movement test? Keep E-stop nearby. Type yes to continue: ")

    if answer.lower() != "yes":
        print("Skipped head movement test.")
        return

    safe_check("Turn robot on", lambda: reachy.turn_on())

    print("Moving head slightly left...")
    safe_check(
        "Head look left",
        lambda: reachy.head.look_at(x=0.5, y=0.15, z=0.0, duration=1.5)
    )
    time.sleep(2)

    print("Returning head to center...")
    safe_check(
        "Head center",
        lambda: reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)
    )
    time.sleep(2)

    print("Head control test complete.")


def check_camera_access(reachy):
    print_section("Camera access")

    safe_check("Camera object", lambda: reachy.cameras)

    print("\nTrying to inspect camera object attributes:")
    try:
        camera_attrs = [
            attr for attr in dir(reachy.cameras)
            if not attr.startswith("_")
        ]
        for attr in camera_attrs:
            print("-", attr)
    except Exception as e:
        print("Cannot list camera attributes:", e)

    answer = input("\nTry to capture one camera frame? Type yes to continue: ")

    if answer.lower() != "yes":
        print("Skipped camera capture.")
        return

    try:
        from reachy2_sdk.media.camera import CameraView
        from PIL import Image
        from pathlib import Path

        output_dir = Path("camera_output")
        output_dir.mkdir(exist_ok=True)

        # Most common camera access path for Reachy2 SDK
        frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)

        img = Image.fromarray(frame[:, :, ::-1])
        output_path = output_dir / "teleop_left_frame.png"
        img.save(output_path)

        print("[OK] Camera frame captured")
        print("Saved to:", output_path)
        print("Timestamp:", timestamp)

    except Exception as e:
        print("[FAILED] Camera capture")
        print("Error:", e)
        print("This may be due to camera service, SDK version, or a different camera API path.")


def check_mobile_base_status_only(reachy):
    print_section("Mobile base status only")

    print("No movement command will be sent.")

    if not hasattr(reachy, "mobile_base"):
        print("[INFO] mobile_base attribute not found.")
        return

    safe_check("Mobile base object", lambda: reachy.mobile_base)

    if hasattr(reachy.mobile_base, "get_current_odometry"):
        safe_check("Mobile base odometry", lambda: reachy.mobile_base.get_current_odometry())
    else:
        print("[INFO] get_current_odometry() not found.")


def main():
    print_section("Connecting to Reachy")

    reachy = ReachySDK(host=ROBOT_HOST)

    print("Connected:", reachy.is_connected())

    if not reachy.is_connected():
        print("Cannot connect. Check IP, network, and reachy2-core.")
        return

    list_possible_attributes(reachy)
    check_basic_robot_parts(reachy)
    check_motor_read_access(reachy)
    check_camera_access(reachy)
    check_mobile_base_status_only(reachy)
    check_small_head_control(reachy)

    print_section("Diagnostic complete")
    print("If head/arms are OK but mic/speaker are not listed, they may not be exposed by this SDK version.")
    print("If camera capture fails but camera object exists, check WebRTC/camera service and SDK camera API.")


if __name__ == "__main__":
    main()