"""API service configuration — reads from a YAML file and environment variables."""

import os
from pathlib import Path

import yaml


class ApiConfig:
    """Load service configuration from a YAML file.

    The config file path is taken from the ``TASK_CONFIG_PATH`` environment
    variable, defaulting to ``/app/config/config.yaml`` (the Docker standard).
    Secrets are read from environment variables and never stored in the YAML file.
    """

    def __init__(self) -> None:
        config_path = Path(os.getenv("TASK_CONFIG_PATH", "/app/config/config.yaml"))
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found at {config_path}. "
                "Set TASK_CONFIG_PATH or provide the file at the default location."
            )
        data: dict = yaml.safe_load(config_path.read_text()) or {}
        self.base_dir = Path(data["base_dir"])
