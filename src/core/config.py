from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_yaml(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file_handle:
        loaded = yaml.safe_load(file_handle)

    if not isinstance(loaded, dict):
        raise ValueError(f"Expected {config_path} to contain a mapping at the top level.")

    return loaded
