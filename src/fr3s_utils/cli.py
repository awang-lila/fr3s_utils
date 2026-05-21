
import time
import rich_click as click

from franky.robot_web_session import  RobotWebSession


robot_configs = {
    "left": {"username": "dex-franka", "password": "franka123", "hostname": "left-box"},
    "right": {"username": "dex-franka", "password": "franka123", "hostname": "right-box"}
}
TIMEOUT = 10
SLEEP_TIME = 5

@click.group()
def cli():
   pass

@cli.command()
@click.option("--force", is_flag=True, default=True)
@click.option("--timeout", default=TIMEOUT)
def unlock(force: bool, timeout: int):
    for robot_name, robot_config in robot_configs.items():
        hostname, username, password = robot_config["hostname"], robot_config["username"], robot_config["password"]
        print(f"Activating {robot_name} ({password}@{hostname})", end="", flush=True)
        with RobotWebSession(hostname, username=username, password=password) as robot:
            print(".", end="", flush=True)
            robot.take_control(force=force, wait_timeout=timeout)
            if robot.has_control():
                print(".", end="", flush=True)
                robot.unlock_brakes()
                print(".", end="", flush=True)
                time.sleep(SLEEP_TIME)
                robot.enable_fci()
                print(".")
                print("Done.")
            else:
                print("Failed.")

@cli.command()
@click.option("--force", is_flag=True, default=True)
@click.option("--timeout", default=TIMEOUT)
def lock(force: bool, timeout: int):
    for robot_name, robot_config in robot_configs.items():
        hostname, username, password = robot_config["hostname"], robot_config["username"], robot_config["password"]
        print(f"Stopping {robot_name} ({password}@{hostname})", end="", flush=True)
        with RobotWebSession(hostname, username=username, password=password) as robot:
            print(".", end="", flush=True)
            robot.take_control(force=force, wait_timeout=timeout)
            print(".", end="", flush=True)
            if robot.has_control():
                robot.lock_brakes()
                print(".")
                print("Done.")
            else:
                print("Failed.")



if __name__ == "__main__":
    cli()
