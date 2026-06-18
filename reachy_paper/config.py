# config.py

ROBOT_HOST = "10.116.19.109"  # Change this to your Reachy IP

# Use "r" for right arm or "l" for left arm
ARM_SIDE = "r"

# Use "left" or "right" camera
CAMERA_SIDE = "left"

# Show OpenCV debug window
SHOW_DEBUG_WINDOW = True

# Paper must stay detected for this many frames before grasping
REQUIRED_STABLE_FRAMES = 10

# Minimum area for white paper detection
MIN_PAPER_AREA = 3000

# Message Reachy will read after handing over the paper
MESSAGE = """
Hello everyone. This paper is for you.
Thank you for watching my Reachy demonstration.
"""