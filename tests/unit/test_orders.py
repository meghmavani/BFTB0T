from __future__ import annotations

from decimal import Decimal

import pytest

from bot.exceptions import BinanceAPIError
from bot.models import OrderRequest, OrderResult, OrderSide
from bot.orders import (
    OrderService,
    build_limit_order_payload,
    build_market_order_payload,
    build_order_payload,
    build_stop_limit_order_payload,
)


def test_build_market_order_payload(market_request: OrderRequest) -> None:
    payload = build_market_order_payload(market_request)

    assert payload == {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.001",
        "newOrderRespType": "RESULT",
    }


def test_build_limit_order_payload(limit_request: OrderRequest) -> None:
    payload = build_limit_order_payload(limit_request)

    assert payload["symbol"] == "BTCUSDT"
    assert payload["side"] == "SELL"
    assert payload["type"] == "LIMIT"
    assert payload["timeInForce"] == "GTC"
    assert payload["price"] == "100000"


def test_build_stop_limit_payload(stop_limit_request: OrderRequest) -> None:
    payload = build_stop_limit_order_payload(stop_limit_request)

    assert payload["type"] == "STOP"
    assert payload["price"] == "99500"
    assert payload["stopPrice"] == "99600"


def test_build_order_payload_dispatches_by_type(limit_request: OrderRequest) -> None:
    payload = build_order_payload(limit_request)
    assert payload["type"] == "LIMIT"


def test_correct_side_mapping() -> None:
    assert OrderSide.BUY.value == "BUY"
    assert OrderSide.SELL.value == "SELL"


def test_order_service_propagates_client_errors(sample_config: object) -> None:
    class FailingClient:
        def place_order(self, request: OrderRequest, payload: dict[str, str]) -> None:
            raise BinanceAPIError("boom", code=-2010)

    service = OrderService(client=FailingClient())

    with pytest.raises(BinanceAPIError):
        service.place_order("BTCUSDT", "BUY", "MARKET", "0.001")


def test_order_service_passes_request_and_payload(limit_request: OrderRequest) -> None:
    captured: dict[str, object] = {}

    class RecordingClient:
        def place_order(
            self, request: OrderRequest, payload: dict[str, str]
        ) -> OrderResult:
            captured["request"] = request
            captured["payload"] = payload
            return OrderResult(
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                price=request.price,
                stop_price=request.stop_price,
                order_id=1,
                status="NEW",
                executed_quantity=Decimal("0"),
                average_price=Decimal("0"),
            )

    service = OrderService(client=RecordingClient())
    result = service.place_order("BTCUSDT", "SELL", "LIMIT", "0.001", price="100000")

    assert result.order_id == 1
    assert isinstance(captured["request"], OrderRequest)
    assert captured["payload"]["type"] == "LIMIT"
