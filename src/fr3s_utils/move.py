import time

import rich_click as click

import numpy as np

from franky import CartesianMotion, Affine, ReferenceType, Robot, JointMotion

from fr3s_utils.config_loader import load_config

_CFG = load_config()
_TIMING = _CFG.get("timing", {})
_HOME_Q = list(
    _CFG.get(
        "home_joint_positions_rad",
        [0.0, 0.0, 0.0, -np.pi / 2.0, 0.0, 1.45, 0.0],
    )
)
_BETWEEN_OUT_AND_BACK_SLEEP_S = float(_TIMING.get("between_out_and_back_sleep_seconds", 0.25))


def _ee_translation_vec(robot: Robot) -> np.ndarray:
    """End-effector origin position in base frame (from current Cartesian pose)."""
    return np.asarray(robot.current_pose.end_effector_pose.translation, dtype=float).reshape(3)


def _rotation_base_from_ee(robot: Robot) -> np.ndarray:
    """Rotation R such that displacement in EE frame Δp_E moves the origin in base as R @ Δp_E."""
    m = robot.current_pose.end_effector_pose.matrix
    return np.asarray(m[:3, :3], dtype=float)


def _print_movement_check(label: str, commanded_base: np.ndarray, estimated_delta: np.ndarray) -> None:
    err = 1e2  * (estimated_delta - commanded_base)
    print(
        f"{label}\n"
        f"  Commanded Δxyz (m, base): {np.array2string(commanded_base, precision=6)}\n"
        f"  Estimated Δxyz (m):       {np.array2string(estimated_delta, precision=6)}\n"
        f"  Error (est - cmd) (cm):    {np.array2string(err, precision=6)}\n"
        f"  ‖Error‖₂ (cm):            {float(np.linalg.norm(err)):.6f}"
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
@click.option("--dx", type=float, default=-0.2)
@click.option("--dy", type=float, default=0.0)
@click.option("--dz", type=float, default=0.0)
@click.option("--relative_dynamics_factor", type=float, default=0.25)
@click.option(
    "--check-movement/--no-check-movement",
    default=True,
    help=(
        "After each relative segment, compare the motion to the change in reported EE position "
        "in the base frame. The commanded translation is rotated from EE-relative axes "
        "(ReferenceType.Relative) into base using the EE pose at motion start."
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
        R_before_out = _rotation_base_from_ee(robot) if check_movement else None

        # Move the robot out (translation is along EE-fixed axes).
        motion1 = CartesianMotion(Affine(motion_vec), ReferenceType.Relative)
        robot.move(motion1)

        if check_movement:
            t1 = _ee_translation_vec(robot)
            cmd_base_out = R_before_out @ motion_vec.reshape(3)
            _print_movement_check("Out segment:", cmd_base_out, t1 - t0)

        time.sleep(_BETWEEN_OUT_AND_BACK_SLEEP_S)

        # Move the robot back.
        R_before_back = _rotation_base_from_ee(robot) if check_movement else None
        motion2 = CartesianMotion(Affine(-1.0 * motion_vec), ReferenceType.Relative)
        robot.move(motion2)

        if check_movement:
            t2 = _ee_translation_vec(robot)
            cmd_base_back = R_before_back @ (-motion_vec).reshape(3)
            _print_movement_check("Back segment:", cmd_base_back, t2 - t1)

    except Exception as e:
        print(f"Error occurred: {e}")
        if robot is not None:
            robot.stop()
        return -1


if __name__ == "__main__":
    cli()
