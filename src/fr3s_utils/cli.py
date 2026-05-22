from __future__ import annotations

import time

import rich_click as click

from franky.robot_web_session import RobotWebSession

from fr3s_utils.config_loader import load_config
from fr3s_utils.unlock_utils import resolve_lock_pairs, resolve_unlock_pairs

_cfg = load_config()
_timing = _cfg.get("timing", {})
robot_configs = _cfg.get("robots", {})
TIMEOUT = int(_timing.get("unlock_timeout_seconds", 10))
SLEEP_TIME = float(_timing.get("unlock_pause_before_enable_fci_seconds", 5))


@click.group()
def cli():
    pass


@cli.command()
@click.option("--force", is_flag=True, default=True)
@click.option("--timeout", type=int, default=TIMEOUT)
def unlock(force: bool, timeout: int):
    pairs = resolve_unlock_pairs(robot_configs, connect_timeout=float(timeout))
    for robot_name, robot_config in pairs:
        hostname, username, password = (
            robot_config["hostname"],
            robot_config["username"],
            robot_config["password"],
        )
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
@click.option("--timeout", type=int, default=TIMEOUT)
def lock(force: bool, timeout: int):
    pairs = resolve_lock_pairs(robot_configs, connect_timeout=float(timeout))
    for robot_name, robot_config in pairs:
        hostname, username, password = (
            robot_config["hostname"],
            robot_config["username"],
            robot_config["password"],
        )
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
