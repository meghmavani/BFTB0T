from __future__ import annotations

from pathlib import Path

import pytest

from bot.config import AppConfig, load_config
from bot.exceptions import ConfigurationError


def test_load_config_from_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BINANCE_API_KEY", "env-key")
    monkeypatch.setenv("BINANCE_API_SECRET", "env-secret")
    monkeypatch.setenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    monkeypatch.setenv("BINANCE_RECV_WINDOW", "7000")
    monkeypatch.setenv("BINANCE_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("BINANCE_LOG_DIR", str(tmp_path))

    config = load_config()

    assert config.api_key == "env-key"
    assert config.api_secret == "env-secret"
    assert config.recv_window == 7000
    assert config.timeout_seconds == 12.5
    assert config.log_dir == tmp_path


def test_load_config_from_env_file(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BINANCE_API_KEY=file-key\n"
        "BINANCE_API_SECRET=file-secret\n"
        "BINANCE_BASE_URL=https://testnet.binancefuture.com\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)

    config = load_config(env_file=env_file)

    assert config.api_key == "file-key"
    assert config.api_secret == "file-secret"


def test_missing_credential_detection(monkeypatch) -> None:
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)

    with pytest.raises(ConfigurationError):
        load_config()


def test_invalid_base_url_rejected(monkeypatch) -> None:
    monkeypatch.setenv("BINANCE_API_KEY", "env-key")
    monkeypatch.setenv("BINANCE_API_SECRET", "env-secret")
    monkeypatch.setenv("BINANCE_BASE_URL", "not-a-url")

    with pytest.raises(ConfigurationError):
        load_config()


def test_app_config_validation_rejects_invalid_timeout() -> None:
    config = AppConfig(
        api_key="k",
        api_secret="s",
        timeout_seconds=0,
    )

    with pytest.raises(ConfigurationError):
        config.validate()
