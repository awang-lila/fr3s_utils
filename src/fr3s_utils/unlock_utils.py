"""Desk login probing and reachable-arm selection for lock and unlock."""

from __future__ import annotations

import sys
from typing import Any

import rich_click as click

from franky.robot_web_session import RobotWebSession

from fr3s_utils.arm_selection import require_configured_robots


def probe_robot_login(
    hostname: str,
    username: str,
    password: str,
    *,
    connect_timeout: float,
) -> bool:
    """Return True if the Desk API accepts a login over HTTPS."""
    robot = RobotWebSession(hostname, username=username, password=password)
    try:
        robot.open(timeout=connect_timeout)
    except Exception:
        return False
    try:
        robot.close()
    except Exception:
        pass
    return True


def reachable_robot_pairs_by_desk(
    robot_configs: dict[str, dict[str, Any]],
    *,
    connect_timeout: float,
) -> tuple[list[tuple[str, dict[str, Any]]], list[str]]:
    """
    Return reachable (name, config) tuples in configured sort order plus names that
    failed the Desk HTTPS login probe.
    """
    require_configured_robots(robot_configs)
    sorted_names = sorted(robot_configs.keys())
    available: list[tuple[str, dict[str, Any]]] = []
    unavailable_names: list[str] = []

    for name in sorted_names:
        cfg = robot_configs[name]
        hostname = cfg["hostname"]
        username = cfg["username"]
        password = cfg["password"]
        if probe_robot_login(
            hostname, username, password, connect_timeout=connect_timeout
        ):
            available.append((name, cfg))
        else:
            unavailable_names.append(name)

    return available, unavailable_names


def resolve_lock_pairs(
    robot_configs: dict[str, dict[str, Any]],
    *,
    connect_timeout: float,
) -> list[tuple[str, dict[str, Any]]]:
    """Reachable robots only; no prompts. Errors if Desk login succeeds for none."""
    available, _unreachable = reachable_robot_pairs_by_desk(
        robot_configs, connect_timeout=connect_timeout
    )
    if not available:
        sorted_names = sorted(robot_configs.keys())
        tried = ", ".join(sorted_names)
        raise click.UsageError(
            "No arms are available: login failed for every configured arm "
            f"({tried}). Check network, power, and credentials in config."
        )
    return available


def resolve_unlock_pairs(
    robot_configs: dict[str, dict[str, Any]],
    *,
    connect_timeout: float,
) -> list[tuple[str, dict[str, Any]]]:
    available, unavailable_names = reachable_robot_pairs_by_desk(
        robot_configs, connect_timeout=connect_timeout
    )

    if not available:
        sorted_names = sorted(robot_configs.keys())
        tried = ", ".join(sorted_names)
        raise click.UsageError(
            "No arms are available: login failed for every configured arm "
            f"({tried}). Check network, power, and credentials in config."
        )

    if unavailable_names:
        reach = ", ".join(n for n, _ in available)
        unreached = ", ".join(unavailable_names)
        summary = (
            "Not all configured arms are reachable.\n"
            f"  Reachable: {reach}\n"
            f"  Unreachable: {unreached}\n"
            "Proceed with unlocking only the reachable arm(s)?"
        )
        if not sys.stdin.isatty():
            raise click.UsageError(
                "Not all configured arms are reachable "
                f"(reachable: {reach}; unreachable: {unreached}). "
                "Fix connectivity or run from an interactive terminal to confirm "
                "unlocking only reachable arms."
            )
        if not click.confirm(summary.rstrip("\n"), default=False):
            raise click.Abort()

    return available
