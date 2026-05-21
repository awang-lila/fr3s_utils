import rich_click as click

import numpy as np

from franky import CartesianMotion, Affine, ReferenceType, Robot, JointMotion

from fr3s_utils.config_loader import load_config

_CFG = load_config()
_HOME_Q = list(
    _CFG.get(
        "home_joint_positions_rad",
        [0.0, 0.0, 0.0, -np.pi / 2.0, 0.0, 1.45, 0.0],
    )
)


def _ee_translation_vec(robot: Robot) -> np.ndarray:
    """End-effector origin position in base frame (from current Cartesian pose)."""
    return np.asarray(robot.current_pose.end_effector_pose.translation, dtype=float).reshape(3)


def _print_movement_check(label: str, commanded: np.ndarray, estimated_delta: np.ndarray) -> None:
    err = estimated_delta - commanded
    print(
        f"{label}\n"
        f"  Commanded Δxyz (m):     {np.array2string(commanded, precision=6)}\n"
        f"  Estimated Δxyz (m):    {np.array2string(estimated_delta, precision=6)}\n"
        f"  Error (est - cmd) (m): {np.array2string(err, precision=6)}\n"
        f"  ‖Error‖₂ (m):         {float(np.linalg.norm(err)):.6f}"
    )


@click.group()
def cli():
   pass

@cli.command()
@click.option("--ip", type=str, default="left-box")
@click.option("--relative_dynamics_factor", type=float, default=0.05)
def home(ip: str, relative_dynamics_factor: float):
    # Connect to robot.
    robot = Robot(ip)
    robot.relative_dynamics_factor = relative_dynamics_factor
    motion = JointMotion(np.asarray(_HOME_Q, dtype=float).tolist())
    robot.move(motion)

@cli.command()
@click.option("--ip", type=str, default="left-box")
@click.option("--dx", type=float, default=-0.15)
@click.option("--dy", type=float, default=-0.15)
@click.option("--dz", type=float, default=-0.15)
@click.option("--relative_dynamics_factor", type=float, default=0.05)
@click.option(
    "--check-movement/--no-check-movement",
    default=True,
    help=(
        "After each relative segment, compare commanded translation to the change in "
        "reported EE position (current_pose); print both vectors and error (est - cmd)."
    ),
)
def out_and_back(
    ip: str,
    dx: float,
    dy: float,
    dz: float,
    relative_dynamics_factor: float,
    check_movement: bool,
):
    # Connect to robot
    robot = None
    try:
        robot = Robot(ip)
        robot.relative_dynamics_factor = relative_dynamics_factor
        motion_vec = np.array([dx, dy, dz])

        t0 = _ee_translation_vec(robot) if check_movement else None

        # Move the robot out.
        motion1 = CartesianMotion(Affine(motion_vec), ReferenceType.Relative)
        robot.move(motion1)

        if check_movement:
            t1 = _ee_translation_vec(robot)
            _print_movement_check("Out segment:", motion_vec, t1 - t0)

        # Move the robot back.
        motion2 = CartesianMotion(Affine(-1.0 * motion_vec), ReferenceType.Relative)
        robot.move(motion2)

        if check_movement:
            t2 = _ee_translation_vec(robot)
            cmd_back = -motion_vec
            _print_movement_check("Back segment:", cmd_back, t2 - t1)

    except Exception as e:
        print(f"Error occurred: {e}")
        if robot is not None:
            robot.stop()
        return -1


if __name__ == "__main__":
    cli()
