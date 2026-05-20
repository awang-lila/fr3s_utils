import argparse
import time

import numpy as np

from pylibfranka import ControllerMode, JointPositions, Robot


HOME_POSITION = [0.0, 0.0, 0.0, -np.pi/2.0, 0.0, 2.51, 0.0]
TIME_TO_HOME = 5.0

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="localhost", help="Robot IP address")
    args = parser.parse_args()

    # Connect to robot
    robot = Robot(args.ip)

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

        # Start joint position control with external control loop
        active_control = robot.start_joint_position_control(ControllerMode.CartesianImpedance)

        initial_position = [0.0] * 7
        time_elapsed = 0.0
        motion_finished = False

        # External control loop
        while not motion_finished:
            # Read robot state and duration
            robot_state, duration = active_control.readOnce()

            # Update time
            time_elapsed += duration.to_sec()

            # On first iteration, capture initial position
            if time_elapsed <= duration.to_sec():
                initial_position = robot_state.q_d if hasattr(robot_state, "q_d") else robot_state.q

            traj_frac = time_elapsed / TIME_TO_HOME
            new_positions = (1.0 - traj_frac) * np.asarray(initial_position) + (traj_frac) * np.asarray(HOME_POSITION)
            # Set joint positions
            joint_positions = JointPositions(new_positions)

            # Set motion_finished flag to True on the last update
            if time_elapsed >= TIME_TO_HOME:
                joint_positions.motion_finished = True
                motion_finished = True
                print("Finished motion, shutting down example")

            # Send command to robot
            active_control.writeOnce(joint_positions)

    except Exception as e:
        print(f"Error occurred: {e}")
        if robot is not None:
            robot.stop()
        return -1


if __name__ == "__main__":
    main()
