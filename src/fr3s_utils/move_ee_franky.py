"""Translate the end-effector out and back using franky `CartesianWaypointMotion` (not manual FCI loops)."""

from typing import Optional

import numpy as np
import rich_click as click

from franky import (
    Affine,
    CartesianState,
    CartesianWaypoint,
    CartesianWaypointMotion,
    ControllerMode,
    Duration,
    RealtimeConfig,
    ReferenceType,
    Robot,
    RobotPose,
)


def _translate_in_base(base: Affine, dx: float, dy: float, dz: float) -> Affine:
    """Apply a base-frame translation to the 4x4 pose (same idea as editing ``O_T_EE`` in ``move_ee``)."""
    m = np.array(base.matrix, copy=True, dtype=np.float64)
    m[0, 3] += dx
    m[1, 3] += dy
    m[2, 3] += dz
    return Affine(m)


def _duration_from_seconds(seconds: float) -> Duration:
    """Franky ``Duration`` uses integer milliseconds; keep at least 1 ms when non-zero."""
    if seconds <= 0:
        return Duration(0)
    ms = int(seconds * 1000)
    return Duration(ms if ms > 0 else 1)


@click.command()
@click.option("--ip", type=str, default="left-box")
@click.option("--dx", default=-0.2)
@click.option("--dy", default=-0.2)
@click.option("--dz", default=-0.2)
@click.option(
    "--time",
    default=5.0,
    help="Duration (s) for one movement (out or back); motion lasts roughly twice this plus --pause.",
)
@click.option(
    "--pause",
    default=0.5,
    help="Seconds to hold at full displacement between outbound and return.",
)
def main(ip: str, dx: float, dy: float, dz: float, time: float, pause: float) -> Optional[int]:
    robot: Optional[Robot] = None
    try:
        robot = Robot(
            ip,
            realtime_config=RealtimeConfig.Ignore,
            controller_mode=ControllerMode.JointImpedance,
        )

        lower_torque_thresholds = [20.0, 20.0, 18.0, 18.0, 16.0, 14.0, 12.0]
        upper_torque_thresholds = [20.0, 20.0, 18.0, 18.0, 16.0, 14.0, 12.0]
        lower_force_thresholds = [20.0, 20.0, 20.0, 25.0, 25.0, 25.0]
        upper_force_thresholds = [20.0, 20.0, 20.0, 25.0, 25.0, 25.0]

        robot.set_collision_behavior(
            lower_torque_thresholds,
            upper_torque_thresholds,
            lower_force_thresholds,
            upper_force_thresholds,
        )

        print("WARNING: This example will move the robot!")
        print("Please make sure to have the user stop button at hand!")
        input("Press Enter to continue...")

        start_pose = robot.current_pose
        out_affine = _translate_in_base(start_pose.end_effector_pose, dx, dy, dz)
        out_pose = RobotPose(out_affine, start_pose.elbow_state)

        t_motion = _duration_from_seconds(time)
        t_hold = _duration_from_seconds(pause)

        waypoints = [
            CartesianWaypoint(
                CartesianState(out_pose),
                reference_type=ReferenceType.Absolute,
                minimum_time=t_motion,
                hold_target_duration=t_hold,
            ),
            CartesianWaypoint(
                CartesianState(start_pose),
                reference_type=ReferenceType.Absolute,
                minimum_time=t_motion,
            ),
        ]

        motion = CartesianWaypointMotion(waypoints)
        robot.move(motion)

    except Exception as e:
        print(f"Error occurred: {e}")
        if robot is not None:
            robot.stop()
        return -1

    return None


if __name__ == "__main__":
    main()
