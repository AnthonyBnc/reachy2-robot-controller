# workflows/grasp_workflow.py

from robot.motion import grasp_handover_release


def run_grasp_demo(reachy, label="grasp demonstration"):
    grasp_handover_release(
        reachy,
        label=label,
    )