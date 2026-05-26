# Reachy 2 Custom Python Control README

This README explains the current Reachy 2 custom-control setup, available robot components, safe movement rules, and recommended coding patterns for controlling Reachy with Python.

Current project focus:

- Camera-based interaction
- Head tracking
- Arm gestures
- Hand/gripper control
- Safe human interaction

Current known limitations:

- Mobile base is currently disabled
- Lidar is currently unavailable
- Reachy microphone is not exposed through the SDK
- Reachy speaker is not currently detected by Linux audio

---

## 1. Current confirmed working setup

Use these SDK versions because they matched the robot-side core container during testing:

```txt
reachy2-sdk==1.0.7
reachy2-sdk-api==1.0.11
```

Recommended Python version:

```txt
Python 3.10.x or Python 3.11.x
```

Avoid Python 3.13 or 3.14 for this project because some dependencies, especially `grpcio`, may fail to install or build.

---

## 2. requirements.txt

Create a `requirements.txt` file with:

```txt
reachy2-sdk==1.0.7
reachy2-sdk-api==1.0.11
opencv-python
numpy
pillow
keyboard
```

Install:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

---

## 3. Basic connection test

Update `ROBOT_HOST` if the robot IP changes.

```python
from reachy2_sdk import ReachySDK

ROBOT_HOST = "10.116.19.109"

reachy = ReachySDK(host=ROBOT_HOST)

print("Connected:", reachy.is_connected())

if reachy.is_connected():
    print("Head:", reachy.head)
    print("Right arm:", reachy.r_arm)
    print("Left arm:", reachy.l_arm)
    print("Cameras:", reachy.cameras)
```

Expected output:

```txt
Connected: True
```

---

## 4. Components you can use now

| Component | Available now? | What you can do |
|---|---:|---|
| Head / neck | Yes | Look left/right/up/down, face tracking |
| Right arm | Yes | Read and move 7 joints |
| Left arm | Yes | Read and move 7 joints |
| Hands / grippers | Yes, if gripper object exists | Open, close, half-open |
| Teleop camera | Yes | Real-time camera stream |
| Depth camera | Detected | Test depth frame access |
| Joint sensors | Yes | Read present and goal positions |
| Mobile base | No | Disabled with `mobile_base: null` |
| Lidar | No | `/dev/rplidar_s2` missing |
| Microphone | Not exposed | No SDK mic attribute found |
| Speaker | Not detected | Linux audio says no sound card |

---

## 5. Available input and output sources

### Inputs

```txt
- Teleop camera frames
- Depth camera object, if frame access works
- Head joint positions
- Right arm joint positions
- Left arm joint positions
- Gripper state, if available
- Keyboard input from computer
- Meta headset or PC microphone, externally through Windows
```

### Outputs

```txt
- Head movement
- Right arm movement
- Left arm movement
- Gripper open/close
- Camera display on computer
- PC or Meta headset audio output
```

---

## 6. Head / neck control

The head is controlled with:

```python
reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)
```

### Meaning of `x`, `y`, `z`, and `duration`

```txt
x = forward target distance
y = left/right target direction
z = up/down target direction
duration = movement time in seconds
```

Typical commands:

```python
# Center/front
reachy.head.look_at(x=0.5, y=0.0, z=0.0, duration=1.5)

# Slightly left
reachy.head.look_at(x=0.5, y=0.20, z=0.0, duration=1.5)

# Slightly right
reachy.head.look_at(x=0.5, y=-0.20, z=0.0, duration=1.5)

# Slightly up
reachy.head.look_at(x=0.5, y=0.0, z=0.15, duration=1.5)

# Slightly down
reachy.head.look_at(x=0.5, y=0.0, z=-0.10, duration=1.5)
```

### Conservative safe head limits

These are project safety limits, not official mechanical limits.

```txt
x: 0.4 to 0.7
y: -0.25 to 0.25
z: -0.15 to 0.20
duration: 0.5 to 3.0 seconds
```

Recommended standard setup:

```txt
x = 0.5
y = -0.20 to 0.20
z = -0.10 to 0.15
duration = 1.0 to 2.0
```

Avoid:

```txt
- Very large y or z values
- duration below 0.3 seconds
- sending repeated head commands too quickly
```

Safe helper:

```python
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def safe_look_at(reachy, x=0.5, y=0.0, z=0.0, duration=1.5):
    x = clamp(x, 0.4, 0.7)
    y = clamp(y, -0.25, 0.25)
    z = clamp(z, -0.15, 0.20)
    duration = clamp(duration, 0.5, 3.0)

    return reachy.head.look_at(x=x, y=y, z=z, duration=duration)
```

---

## 7. Arm control

Each arm has 7 joint values.

```txt
0 = shoulder pitch
1 = shoulder roll
2 = elbow yaw
3 = elbow pitch
4 = wrist roll
5 = wrist pitch
6 = wrist yaw
```

Read current arm positions:

```python
right_current = reachy.r_arm.get_current_positions()
left_current = reachy.l_arm.get_current_positions()
```

Move an arm:

```python
reachy.r_arm.goto(target_positions, duration=2.0, wait=True)
reachy.l_arm.goto(target_positions, duration=2.0, wait=True)
```

---

## 8. Conservative arm motion limits

Because exact robot-specific mechanical limits should be confirmed from the official robot configuration, use relative movement limits for demos instead of aggressive hard-coded absolute poses.

### Safe relative limits for demos

```txt
Shoulder pitch: max +/- 20 degrees from current
Shoulder roll: max +/- 25 degrees from current
Elbow yaw: max +/- 20 degrees from current
Elbow pitch: max +/- 25 degrees from current
Wrist roll: max +/- 30 degrees from current
Wrist pitch: max +/- 20 degrees from current
Wrist yaw: max +/- 30 degrees from current
duration: 1.0 to 3.0 seconds
```

For first-time testing:

```txt
Shoulder joints: +/- 10 degrees
Elbow joints: +/- 10 to 15 degrees
Wrist joints: +/- 15 degrees
duration: 2.0 seconds
```

Safe helper:

```python
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def safe_relative_arm_pose(current, deltas):
    """
    current: list of 7 current joint positions
    deltas: list of 7 requested relative changes

    Returns a safe target pose.
    """

    max_deltas = [
        20,  # shoulder pitch
        25,  # shoulder roll
        20,  # elbow yaw
        25,  # elbow pitch
        30,  # wrist roll
        20,  # wrist pitch
        30,  # wrist yaw
    ]

    target = current.copy()

    for i in range(7):
        safe_delta = clamp(deltas[i], -max_deltas[i], max_deltas[i])
        target[i] = current[i] + safe_delta

    return target
```

Example:

```python
current = reachy.r_arm.get_current_positions()

target = safe_relative_arm_pose(
    current,
    deltas=[-15, 20, 0, -20, 0, -5, 10]
)

reachy.r_arm.goto(target, duration=2.0, wait=True)
```

---

## 9. Hands / grippers

Open and close the gripper:

```python
reachy.r_arm.gripper.set_opening(100)  # fully open
reachy.r_arm.gripper.set_opening(50)   # half open
reachy.r_arm.gripper.set_opening(0)    # fully closed
```

Recommended safe values:

```txt
100 = open hand
50 = half open
30 to 40 = gentle close for demo
0 = fully closed, avoid near human fingers
```

Safe helper:

```python
def safe_set_gripper(gripper, value):
    value = max(0, min(100, value))
    return gripper.set_opening(value)
```

Avoid closing fully on a human hand or fragile object.

---

## 10. Camera access

The current setup detects:

```txt
- teleop camera
- depth camera
```

Basic camera frame capture:

```python
from reachy2_sdk.media.camera import CameraView

frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)
```

Real-time camera viewer:

```python
import cv2
from reachy2_sdk.media.camera import CameraView

while True:
    frame, timestamp = reachy.cameras.teleop.get_frame(CameraView.LEFT)

    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("Reachy Camera", frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
```

---

## 11. Face detection interaction design

Recommended design:

```txt
Camera detects face
→ Head tracks face
→ If face is centered for 2 seconds
→ Trigger predefined arm gesture
→ Return arm to saved pose
```

Do not directly map face position to every arm joint. That can be unsafe.

Safe interaction pattern:

```txt
Camera controls head only in real time.
Camera triggers predefined arm gesture only when conditions are safe.
```

Example rules:

```txt
Face left  → head turns left
Face right → head turns right
Face up    → head looks up
Face down  → head looks down
Centered for 2 seconds → wave
No face for 3 seconds → return head to center
```

---

## 12. Safe full-arm greeting gesture

This gesture uses the whole arm but keeps movement relative to the current pose.

```python
def right_arm_greeting_wave(reachy):
    current = reachy.r_arm.get_current_positions()
    home = current.copy()

    raised = safe_relative_arm_pose(
        current,
        deltas=[-20, 25, 0, -25, 0, -5, 10]
    )

    reachy.r_arm.goto(raised, duration=2.0, wait=True)

    try:
        reachy.r_arm.gripper.set_opening(100)
    except Exception:
        pass

    wave_left = safe_relative_arm_pose(raised, deltas=[0, 0, 0, 0, 0, 0, 20])
    wave_right = safe_relative_arm_pose(raised, deltas=[0, 0, 0, 0, 0, 0, -20])

    reachy.r_arm.goto(wave_left, duration=0.8, wait=True)
    reachy.r_arm.goto(wave_right, duration=0.8, wait=True)
    reachy.r_arm.goto(wave_left, duration=0.8, wait=True)

    reachy.r_arm.goto(home, duration=2.0, wait=True)
```

---

## 13. Components currently not recommended

### Mobile base

Do not use mobile base movement yet.

Known issue:

```txt
mobile_base: null
/dev/vesc_wheels missing
/dev/rplidar_s2 missing
SetSpeed not available when mobile base is enabled
```

Avoid:

```python
reachy.mobile_base
```

for movement until the VESC/lidar issue is fixed.

### Microphone and speaker

Current setup does not expose a Reachy microphone or speaker through the SDK.

Recommended workaround:

```txt
Use Meta headset microphone or PC microphone for input.
Use Meta headset speaker or PC speaker for output.
Use Reachy camera and movement for robot interaction.
```

---

## 14. Standard safe startup routine

Before running interaction code:

```txt
1. Make sure E-stop is reachable.
2. Make sure arms have clear space.
3. Keep mobile_base: null until fixed.
4. Open dashboard and confirm robot is responsive.
5. Run Python connection test.
6. Start with head movement only.
7. Then test small arm movement.
8. Then test camera interaction.
```

---

## 15. Standard safety rules for code

Always follow these rules:

```txt
- Never send large joint changes first.
- Always read current pose before moving the arm.
- Always save a home pose before a gesture.
- Always return to home pose after the gesture.
- Use duration >= 1.0 second for arm motion.
- Use duration >= 0.5 second for head motion.
- Avoid moving both arms at the same time until tested.
- Keep the E-stop nearby.
- Do not use mobile base until fixed.
```

Bad pattern:

```python
reachy.r_arm.goto([90, 90, 90, 90, 90, 90, 90], duration=0.2, wait=True)
```

Good pattern:

```python
current = reachy.r_arm.get_current_positions()
target = safe_relative_arm_pose(current, deltas=[-10, 15, 0, -10, 0, 0, 10])
reachy.r_arm.goto(target, duration=2.0, wait=True)
```

---

## 16. Troubleshooting

### SDK cannot connect

Check:

```txt
- Robot IP is correct
- Computer and robot are on the same network
- reachy2-core is running
- Dashboard opens
```

### API version mismatch

Use:

```txt
reachy2-sdk==1.0.7
reachy2-sdk-api==1.0.11
```

### Camera fails with PIL error

Install Pillow:

```bash
python -m pip install pillow
```

### Camera window does not open

Install OpenCV:

```bash
python -m pip install opencv-python
```

### Mobile base errors

Known issue:

```txt
SetSpeed not available
/dev/vesc_wheels missing
/dev/rplidar_s2 missing
```

Keep this in the robot YAML until fixed:

```yaml
mobile_base: null
```

---

## 17. Recommended project architecture

Use this design:

```txt
Reachy camera
→ OpenCV face detection
→ Head tracking
→ Safe predefined arm gesture
→ Gripper open/close
```

For voice:

```txt
Meta headset mic / PC mic
→ Python speech recognition
→ Reachy SDK command
→ PC/Meta speaker output
```

For safety:

```txt
Camera should trigger gestures.
Camera should not directly control all arm joints in real time.
```

---

## 18. Summary

Currently usable:

```txt
- Head / neck movement
- Right arm movement
- Left arm movement
- Hand / gripper control
- Teleop camera
- Depth camera object
- Joint feedback
- Face detection with OpenCV
```

Currently not usable or not recommended:

```txt
- Mobile base
- Lidar
- Reachy microphone
- Reachy speaker
```

Best demo:

```txt
Camera detects person
→ Head follows face
→ Face centered
→ Right arm waves
→ Hand opens
→ Robot returns to safe pose
```
