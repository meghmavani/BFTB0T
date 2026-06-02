from __future__ import annotations

from decimal import Decimal

import cli as cli_module
from bot.exceptions import BinanceAuthenticationError, ValidationError
from bot.models import OrderResult, OrderSide, OrderType
from bot.orders import OrderService


class FakeService:
    def __init__(
        self, result: OrderResult | None = None, error: Exception | None = None
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, object]] = []

    def place_order(self, **kwargs: object) -> OrderResult:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def _sample_result() -> OrderResult:
    return OrderResult(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.001"),
        price=None,
        stop_price=None,
        order_id=123456,
        status="FILLED",
        executed_quantity=Decimal("0.001"),
        average_price=Decimal("65000"),
    )


def test_help_command_output(cli_runner) -> None:
    result = cli_runner.invoke(cli_module.app, ["place-order", "--help"])

    assert result.exit_code == 0
    assert "place-order" in result.output
    assert "--symbol" in result.output
    assert "--type" in result.output


def test_place_order_success(cli_runner, monkeypatch) -> None:
    fake_service = FakeService(result=_sample_result())
    monkeypatch.setattr(cli_module, "create_order_service", lambda config: fake_service)
    monkeypatch.setattr(
        cli_module, "load_config", lambda: cli_module.AppConfig("k", "s")
    )

    result = cli_runner.invoke(
        cli_module.app,
        [
            "place-order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
        ],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "ORDER SUMMARY" in result.output
    assert "ORDER RESPONSE" in result.output
    assert "Order ID" in result.output
    assert fake_service.calls[0]["symbol"] == "BTCUSDT"


def test_place_order_prompts_for_missing_arguments(cli_runner, monkeypatch) -> None:
    fake_service = FakeService(result=_sample_result())
    monkeypatch.setattr(cli_module, "create_order_service", lambda config: fake_service)
    monkeypatch.setattr(
        cli_module, "load_config", lambda: cli_module.AppConfig("k", "s")
    )

    result = cli_runner.invoke(
        cli_module.app,
        ["place-order"],
        input="BTCUSDT\nBUY\nMARKET\n0.001\ny\n",
    )

    assert result.exit_code == 0
    assert "Symbol" in result.output
    assert fake_service.calls


def test_place_order_rejects_invalid_arguments(cli_runner, monkeypatch) -> None:
    class DummyClient:
        def place_order(self, request, payload):
            raise AssertionError("client should not be called for invalid input")

    monkeypatch.setattr(
        cli_module, "create_order_service", lambda config: OrderService(DummyClient())
    )
    monkeypatch.setattr(
        cli_module, "load_config", lambda: cli_module.AppConfig("k", "s")
    )

    result = cli_runner.invoke(
        cli_module.app,
        [
            "place-order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "-1",
        ],
        input="y\n",
    )

    assert result.exit_code == 1
    assert "Validation error" in result.output
    assert "greater than zero" in result.output


def test_place_order_confirmation_flow(cli_runner, monkeypatch) -> None:
    fake_service = FakeService(result=_sample_result())
    monkeypatch.setattr(cli_module, "create_order_service", lambda config: fake_service)
    monkeypatch.setattr(
        cli_module, "load_config", lambda: cli_module.AppConfig("k", "s")
    )

    result = cli_runner.invoke(
        cli_module.app,
        [
            "place-order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
        ],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "Order cancelled by user." in result.output
    assert fake_service.calls == []


def test_place_order_displays_user_friendly_error(cli_runner, monkeypatch) -> None:
    fake_service = FakeService(
        error=BinanceAuthenticationError("Invalid API-key", code=-2015),
    )
    monkeypatch.setattr(cli_module, "create_order_service", lambda config: fake_service)
    monkeypatch.setattr(
        cli_module, "load_config", lambda: cli_module.AppConfig("k", "s")
    )

    result = cli_runner.invoke(
        cli_module.app,
        [
            "place-order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
        ],
        input="y\n",
    )

    assert result.exit_code == 1
    assert "Authentication error" in result.output
    assert "Suggested Action" in result.output


def test_cli_validation_error_path(cli_runner, monkeypatch) -> None:
    fake_service = FakeService(error=ValidationError("bad input"))
    monkeypatch.setattr(cli_module, "create_order_service", lambda config: fake_service)
    monkeypatch.setattr(
        cli_module, "load_config", lambda: cli_module.AppConfig("k", "s")
    )

    result = cli_runner.invoke(
        cli_module.app,
        [
            "place-order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
        ],
        input="y\n",
    )

    assert result.exit_code == 1
    assert "bad input" in result.output
