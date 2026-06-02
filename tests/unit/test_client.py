from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlencode

import httpx
import pytest
import respx

from bot.client import BinanceClient
from bot.exceptions import (
    BinanceAPIError,
    BinanceAuthenticationError,
    BinanceResponseError,
    BinanceTimeoutError,
)
from bot.orders import build_market_order_payload
from tests.fixtures import API_ERROR_RESPONSE, AUTH_ERROR_RESPONSE, MARKET_RESPONSE


def test_client_returns_parsed_response(sample_config, market_request) -> None:
    payload = build_market_order_payload(market_request)
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)

    with respx.mock(assert_all_called=True) as router:
        route = router.post("https://testnet.binancefuture.com/fapi/v1/order")

        def responder(request: httpx.Request) -> httpx.Response:
            params = request.url.params
            signed_payload = {
                "symbol": params["symbol"],
                "side": params["side"],
                "type": params["type"],
                "quantity": params["quantity"],
                "newOrderRespType": params["newOrderRespType"],
                "timestamp": params["timestamp"],
                "recvWindow": params["recvWindow"],
            }
            expected_signature = hmac.new(
                sample_config.api_secret.encode("utf-8"),
                urlencode(signed_payload).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            assert params["signature"] == expected_signature
            return httpx.Response(200, json=MARKET_RESPONSE)

        route.mock(side_effect=responder)
        result = client.place_order(market_request, payload)

    assert result.order_id == 123456
    assert result.status == "FILLED"
    assert result.executed_quantity == result.quantity


def test_client_raises_on_api_error(sample_config, market_request) -> None:
    payload = build_market_order_payload(market_request)
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)

    with respx.mock(assert_all_called=True) as router:
        router.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
            return_value=httpx.Response(400, json=API_ERROR_RESPONSE),
        )

        with pytest.raises(BinanceAPIError) as excinfo:
            client.place_order(market_request, payload)

    assert excinfo.value.code == -2010


def test_client_raises_on_timeout(sample_config, market_request, mocker) -> None:
    payload = build_market_order_payload(market_request)
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)
    mocker.patch.object(
        client._http_client,
        "post",
        side_effect=httpx.TimeoutException("timed out"),
    )

    with pytest.raises(BinanceTimeoutError):
        client.place_order(market_request, payload)


def test_client_raises_on_auth_failure(sample_config, market_request) -> None:
    payload = build_market_order_payload(market_request)
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)

    with respx.mock(assert_all_called=True) as router:
        router.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
            return_value=httpx.Response(401, json=AUTH_ERROR_RESPONSE),
        )

        with pytest.raises(BinanceAuthenticationError):
            client.place_order(market_request, payload)


def test_client_raises_on_malformed_response(sample_config, market_request) -> None:
    payload = build_market_order_payload(market_request)
    client = BinanceClient(sample_config, time_provider=lambda: 1700000000000)

    with respx.mock(assert_all_called=True) as router:
        router.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
            return_value=httpx.Response(200, text="not-json"),
        )

        with pytest.raises(BinanceResponseError):
            client.place_order(market_request, payload)
