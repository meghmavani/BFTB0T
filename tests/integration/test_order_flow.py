from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
import respx

from bot.client import BinanceClient
from bot.orders import OrderService
from tests.fixtures import LIMIT_RESPONSE, MARKET_RESPONSE, STOP_LIMIT_RESPONSE


@pytest.mark.integration
@pytest.mark.parametrize(
    ("side", "order_type", "quantity", "price", "stop_price", "response"),
    [
        ("BUY", "MARKET", "0.001", None, None, MARKET_RESPONSE),
        ("SELL", "LIMIT", "0.001", "100000", None, LIMIT_RESPONSE),
        ("SELL", "STOP_LIMIT", "0.001", "99500", "99600", STOP_LIMIT_RESPONSE),
    ],
)
def test_order_flow_parses_order_result(
    sample_config,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None,
    stop_price: str | None,
    response: dict[str, str | int],
) -> None:
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)
    service = OrderService(client=client)

    with respx.mock(assert_all_called=True) as router:
        router.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
            return_value=httpx.Response(200, json=response),
        )
        result = service.place_order(
            symbol="BTCUSDT",
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

    assert result.symbol == "BTCUSDT"
    assert result.side.value == side
    assert result.order_type.display_value == order_type.replace("_", "-")
    assert result.quantity == Decimal("0.001")
