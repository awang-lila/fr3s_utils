"""Load bundled YAML configuration for fr3s_utils."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml


def _config_path() -> Path:
    return Path(__file__).resolve().parent / "config.yaml"


@functools.lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    path = _config_path()
    with path.open(encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping at root of {path}, got {type(loaded)}")
    return loaded
