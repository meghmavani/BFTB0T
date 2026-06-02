from __future__ import annotations

import httpx
import respx

from bot.client import BinanceClient
from bot.orders import build_limit_order_payload
from tests.fixtures import LIMIT_RESPONSE


def test_binance_client_signs_and_posts_request(sample_config, limit_request) -> None:
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)
    payload = build_limit_order_payload(limit_request)

    with respx.mock(assert_all_called=True) as router:

        def responder(request: httpx.Request) -> httpx.Response:
            params = dict(request.url.params)
            expected_params = client._sign_payload(payload)
            assert params == expected_params
            assert request.url.path == "/fapi/v1/order"
            return httpx.Response(200, json=LIMIT_RESPONSE)

        router.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
            side_effect=responder,
        )
        result = client.place_order(limit_request, payload)

    assert result.order_id == 234567
    assert result.order_type.display_value == "LIMIT"
