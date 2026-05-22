"""Interactive and flag-based arm selection against config.yaml robots map."""

from __future__ import annotations

import sys
from typing import Any

import rich_click as click


def _sorted_keys(robot_configs: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(robot_configs.keys())


def require_configured_robots(robot_configs: dict[str, dict[str, Any]]) -> None:
    if not robot_configs:
        raise click.UsageError(
            "No arms are available: 'robots' in config.yaml is missing or empty. "
            "Configure at least one arm with hostname, username, and password."
        )


def _format_keys_help(robot_configs: dict[str, dict[str, Any]]) -> str:
    keys_sorted = _sorted_keys(robot_configs)
    extras = ", both" if len(keys_sorted) > 1 else ""
    return ", ".join(keys_sorted) + extras


def _match_arm_key(robot_configs: dict[str, dict[str, Any]], arm: str) -> str:
    want = arm.strip().lower()
    for k in robot_configs:
        if k.lower() == want:
            return k
    raise click.UsageError(
        f"Unknown arm '{arm}'. Configured arms: {_format_keys_help(robot_configs)}."
    )


def _parse_arm_flag(robot_configs: dict[str, dict[str, Any]], arm_flag: str) -> list[str]:
    keys_sorted = _sorted_keys(robot_configs)
    al = arm_flag.strip().lower()
    if al == "both":
        if len(keys_sorted) < 2:
            raise click.UsageError(
                "Only one arm is configured; 'both' is not applicable. "
                f"Choose {_format_keys_help(robot_configs)}."
            )
        return list(keys_sorted)
    return [_match_arm_key(robot_configs, arm_flag)]


def _interactive_choose_arms(
    robot_configs: dict[str, dict[str, Any]],
    *,
    question: str,
) -> list[str]:
    """Print inventory, then prompt for one arm key or 'both' when applicable."""
    require_configured_robots(robot_configs)
    keys_sorted = _sorted_keys(robot_configs)

    lines = ["Available arms:"]
    for k in keys_sorted:
        h = robot_configs[k].get("hostname", "?")
        lines.append(f"  {k}  ({h})")
    click.echo("\n".join(lines))

    choices = list(keys_sorted)
    if len(keys_sorted) > 1:
        choices = keys_sorted + ["both"]

    picked = click.prompt(question, type=click.Choice(choices, case_sensitive=False))
    if picked.lower() == "both":
        return list(keys_sorted)
    return [_match_arm_key(robot_configs, picked)]


def resolve_for_move_commands(
    robot_configs: dict[str, dict[str, Any]],
    ip_opt: str | None,
    arm_opt: str | None,
    *,
    interactive_question: str,
) -> list[tuple[str, str]]:
    """
    Returns (logical_label, hostname) for Robot(...).
    Uses '__direct__' as label when connecting via --ip.
    """
    if ip_opt is not None and arm_opt is not None:
        raise click.UsageError("Specify either --ip or --arm, not both.")

    if ip_opt is not None:
        return [("__direct__", ip_opt)]

    require_configured_robots(robot_configs)

    if arm_opt is None:
        if not sys.stdin.isatty():
            raise click.UsageError(
                "No interactive terminal; specify --ip or --arm ("
                + _format_keys_help(robot_configs)
                + ")."
            )
        sel = _interactive_choose_arms(
            robot_configs, question=interactive_question
        )
    else:
        sel = _parse_arm_flag(robot_configs, arm_opt)

    return [(k, str(robot_configs[k]["hostname"])) for k in sel]
