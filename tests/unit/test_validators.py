from __future__ import annotations

from decimal import Decimal

import pytest

from bot.exceptions import ValidationError
from bot.models import OrderType
from bot.validators import (
    validate_order_inputs,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def test_valid_symbol_accepted() -> None:
    assert validate_symbol("btcusdt") == "BTCUSDT"


@pytest.mark.parametrize("symbol", ["", "BTC-USD", "ETHUSD", "ethusdt/usdt"])
def test_invalid_symbol_rejected(symbol: str) -> None:
    with pytest.raises(ValidationError):
        validate_symbol(symbol)


@pytest.mark.parametrize("side", ["BUY", "sell"])
def test_valid_side_accepted(side: str) -> None:
    assert validate_side(side).value in {"BUY", "SELL"}


@pytest.mark.parametrize("side", ["hold", "LONG", "", "123"])
def test_invalid_side_rejected(side: str) -> None:
    with pytest.raises(ValidationError):
        validate_side(side)


def test_valid_quantity_accepted() -> None:
    assert validate_quantity("0.001") == Decimal("0.001")


@pytest.mark.parametrize("quantity", ["0", 0, "-1", Decimal("-0.1")])
def test_zero_or_negative_quantity_rejected(quantity: object) -> None:
    with pytest.raises(ValidationError):
        validate_quantity(quantity)


def test_limit_order_without_price_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_price(None, OrderType.LIMIT)


def test_market_order_does_not_require_price() -> None:
    assert validate_price(None, OrderType.MARKET) is None


def test_stop_limit_requires_price_and_stop_price() -> None:
    with pytest.raises(ValidationError):
        validate_price(None, OrderType.STOP_LIMIT)
    with pytest.raises(ValidationError):
        validate_stop_price(None, OrderType.STOP_LIMIT)


def test_invalid_order_type_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_order_type("iceberg")


def test_validate_order_inputs_builds_normalized_request() -> None:
    request = validate_order_inputs(
        symbol="btcusdt",
        side="buy",
        order_type="market",
        quantity="0.01",
    )

    assert request.symbol == "BTCUSDT"
    assert request.side.value == "BUY"
    assert request.order_type == OrderType.MARKET
    assert request.quantity == Decimal("0.01")
