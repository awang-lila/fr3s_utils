#!/usr/bin/env python3

# Copyright (c) 2025 Franka Robotics GmbH
# Use of this source code is governed by the Apache-2.0 license, see LICENSE

import rich_click as click

import numpy as np

from pylibfranka import CartesianPose, ControllerMode, RealtimeConfig, Robot


def _traj_frac_at_step(i: int, n_steps: int, n_smooth: int) -> float:
    """Interpolation fraction at discrete step index ``i`` (0 .. n_steps-1)."""
    traj_frac = (i + 1) / n_steps
    if i < n_smooth:
        phase = (i + 1) / n_smooth
        traj_frac = np.sin(phase * np.pi / 2) * traj_frac
    return traj_frac


@click.group()
def cli():
   pass

@cli.command()
@click.option("--ip", type=str, default="left-box")
@click.option("--dx", default=-0.2)
@click.option("--dy", default=-0.2)
@click.option("--dz", default=-0.2)
@click.option(
    "--time",
    default=5.0,
    help="Duration (s) for one movement (out or back); motion lasts twice this plus --pause.",
)
@click.option(
    "--pause",
    default=0.5,
    help="Seconds to hold at full displacement between outbound and return (control-rate dwell).",
)
@click.option("--dt", default=1e-3)
@click.option("--n_smooth", default=500)
def main(
    ip: str,
    dx: float,
    dy: float,
    dz: float,
    time: float,
    pause: float,
    dt: float,
    n_smooth: int,
):
    # Connect to robot
    robot = Robot(ip, RealtimeConfig.kIgnore)

    try:
        # Set collision behavior
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

        # First move the robot to a suitable joint configuration
        print("WARNING: This example will move the robot!")
        print("Please make sure to have the user stop button at hand!")
        input("Press Enter to continue...")

        # Start cartesian pose control with external control loop
        active_control = robot.start_cartesian_pose_control(ControllerMode.JointImpedance)

        robot_state, duration = active_control.readOnce()
        initial_cartesian_pose = robot_state.O_T_EE

        n_half = max(1, int(time / dt))
        pause_steps = max(0, int(pause / dt))
        hold_frac = _traj_frac_at_step(n_half - 1, n_half, n_smooth)

        def step_pose(traj_frac: float) -> None:
            active_control.readOnce()
            new_cartesian_pose = initial_cartesian_pose.copy()
            new_cartesian_pose[12] += dx * traj_frac
            new_cartesian_pose[13] += dy * traj_frac
            new_cartesian_pose[14] += dz * traj_frac
            active_control.writeOnce(CartesianPose(new_cartesian_pose))

        for i in range(n_half):
            step_pose(_traj_frac_at_step(i, n_half, n_smooth))

        for _ in range(pause_steps):
            step_pose(hold_frac)

        for i in range(n_half):
            step_pose(_traj_frac_at_step(n_half - 1 - i, n_half, n_smooth))

    except Exception as e:
        print(f"Error occurred: {e}")
        if robot is not None:
            robot.stop()
        return -1


if __name__ == "__main__":
    main()
