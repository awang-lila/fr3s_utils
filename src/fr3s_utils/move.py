import rich_click as click

import numpy as np

from franky import CartesianMotion, Affine, ReferenceType, Robot, JointMotion


@click.group()
def cli():
   pass

@cli.command()
@click.option("--ip", type=str, default="left-box")
@click.option("--relative_dynamics_factor", default=0.05)
def home(ip: str, relative_dynamics_factor: float):
    # Connect to robot.
    robot = Robot(ip)
    robot.relative_dynamics_factor = relative_dynamics_factor
    motion = JointMotion([0.0, 0.0, 0.0, -np.pi / 2.0, 0.0, 1.45, 0.0])
    robot.move(motion)

@cli.command()
@click.option("--ip", type=str, default="left-box")
@click.option("--dx", default=-0.15)
@click.option("--dy", default=-0.15)
@click.option("--dz", default=-0.15)
@click.option("--relative_dynamics_factor", default=0.05)
def out_and_back(
    ip: str,
    dx: float,
    dy: float,
    dz: float,
    relative_dynamics_factor: float
):
    # Connect to robot
    robot = Robot(ip)
    robot.relative_dynamics_factor = relative_dynamics_factor
    try:
        motion_vec = np.array([dx, dy, dz])

        # Move the robot out.
        motion1 = CartesianMotion(Affine(motion_vec), ReferenceType.Relative)
        robot.move(motion1)

        # Move the robot back.
        motion2 = CartesianMotion(Affine(-1.0 * motion_vec), ReferenceType.Relative)
        robot.move(motion2)

    except Exception as e:
        print(f"Error occurred: {e}")
        if robot is not None:
            robot.stop()
        return -1


if __name__ == "__main__":
    cli()
