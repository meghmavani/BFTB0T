"""Configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values

from .exceptions import ConfigurationError

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_LOG_DIR = Path("logs")


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Runtime configuration for the application."""

    api_key: str
    api_secret: str
    base_url: str = DEFAULT_BASE_URL
    recv_window: int = 5000
    timeout_seconds: float = 10.0
    log_dir: Path = DEFAULT_LOG_DIR

    def validate(self) -> None:
        """Validate the config values."""

        if not self.api_key.strip():
            raise ConfigurationError("BINANCE_API_KEY is missing.")
        if not self.api_secret.strip():
            raise ConfigurationError("BINANCE_API_SECRET is missing.")

        parsed_url = urlparse(self.base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ConfigurationError("Base URL is invalid.")

        if self.recv_window <= 0:
            raise ConfigurationError("recv_window must be positive.")

        if self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be positive.")


def load_config(env_file: str | Path | None = None) -> AppConfig:
    """Load configuration from the environment.

    If *env_file* is supplied, it is read without mutating the process-wide
    environment so tests remain deterministic.
    """

    file_values: dict[str, str] = {}
    if env_file is not None:
        file_values = {
            key: value
            for key, value in dotenv_values(Path(env_file)).items()
            if value is not None
        }

    def _read(key: str, default: str) -> str:
        return os.getenv(key, file_values.get(key, default))

    config = AppConfig(
        api_key=_read("BINANCE_API_KEY", ""),
        api_secret=_read("BINANCE_API_SECRET", ""),
        base_url=_read("BINANCE_BASE_URL", DEFAULT_BASE_URL),
        recv_window=int(_read("BINANCE_RECV_WINDOW", "5000")),
        timeout_seconds=float(_read("BINANCE_TIMEOUT_SECONDS", "10.0")),
        log_dir=Path(_read("BINANCE_LOG_DIR", str(DEFAULT_LOG_DIR))),
    )
    config.validate()
    return config
