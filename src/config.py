from pathlib import Path

import yaml

CONFIG_PATH = Path("config.yaml")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.yaml not found. Copy config.yaml.example and fill in your settings."
        )
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)
