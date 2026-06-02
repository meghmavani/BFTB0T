"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bot.config import AppConfig

from .fixtures import LIMIT_REQUEST, MARKET_REQUEST, STOP_LIMIT_REQUEST, TEST_CONFIG


@pytest.fixture()
def sample_config(tmp_path: Path) -> AppConfig:
    """Return a config with a temporary log directory."""

    return AppConfig(
        api_key=TEST_CONFIG.api_key,
        api_secret=TEST_CONFIG.api_secret,
        base_url=TEST_CONFIG.base_url,
        recv_window=TEST_CONFIG.recv_window,
        timeout_seconds=TEST_CONFIG.timeout_seconds,
        log_dir=tmp_path,
    )


@pytest.fixture()
def market_request() -> object:
    return MARKET_REQUEST


@pytest.fixture()
def limit_request() -> object:
    return LIMIT_REQUEST


@pytest.fixture()
def stop_limit_request() -> object:
    return STOP_LIMIT_REQUEST


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()
