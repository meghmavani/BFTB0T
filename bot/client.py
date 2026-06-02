"""Binance Futures API client."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlencode

import httpx

from .config import AppConfig
from .exceptions import (
    BinanceAPIError,
    BinanceAuthenticationError,
    BinanceNetworkError,
    BinanceResponseError,
    BinanceTimeoutError,
)
from .models import OrderRequest, OrderResult


class BinanceClient:
    """HTTP client responsible for signed Binance order requests."""

    def __init__(
        self,
        config: AppConfig,
        http_client: httpx.Client | None = None,
        time_provider: Callable[[], int] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client or httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers={"X-MBX-APIKEY": config.api_key},
        )
        self._time_provider = time_provider or self._default_time_provider
        self._logger = logger or logging.getLogger("trading_bot.client")

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self._http_client.close()

    def __enter__(self) -> BinanceClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def place_order(
        self, request: OrderRequest, payload: Mapping[str, str]
    ) -> OrderResult:
        """Submit a signed order to Binance and parse the response."""

        signed_payload = self._sign_payload(payload)
        self._logger.info(
            "Submitting order symbol=%s side=%s type=%s quantity=%s",
            request.symbol,
            request.side.value,
            request.order_type.display_value,
            request.quantity,
        )

        try:
            response = self._http_client.post("/fapi/v1/order", params=signed_payload)
        except httpx.TimeoutException as exc:
            self._logger.exception("Timeout while placing order")
            raise BinanceTimeoutError(
                "Binance request timed out.",
                details={"symbol": request.symbol},
            ) from exc
        except httpx.RequestError as exc:
            self._logger.exception("Network failure while placing order")
            raise BinanceNetworkError(
                "Network failure while contacting Binance.",
                details={"symbol": request.symbol},
            ) from exc

        if response.status_code in {401, 403}:
            error = self._parse_error_response(response)
            self._logger.error(
                "Authentication failure placing order: %s", error.message
            )
            raise BinanceAuthenticationError(
                error.message,
                code=error.code,
                status_code=response.status_code,
                details=error.details,
            )

        if not response.is_success:
            error = self._parse_error_response(response)
            self._logger.error(
                "Binance rejected order symbol=%s status=%s error=%s",
                request.symbol,
                response.status_code,
                error,
            )
            raise error

        data = self._parse_json(response)
        result = OrderResult.from_binance_response(data, request)
        self._logger.info(
            "Order accepted order_id=%s status=%s executed_quantity=%s avg_price=%s",
            result.order_id,
            result.status,
            result.executed_quantity,
            result.average_price,
        )
        return result

    def _sign_payload(self, payload: Mapping[str, str]) -> dict[str, str]:
        """Add timestamp and HMAC signature to the outgoing payload."""

        signed_payload: dict[str, str] = {
            key: str(value) for key, value in payload.items()
        }
        signed_payload["timestamp"] = str(self._time_provider())
        signed_payload["recvWindow"] = str(self._config.recv_window)

        query_string = urlencode(signed_payload)
        signature = hmac.new(
            self._config.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed_payload["signature"] = signature
        return signed_payload

    def _parse_json(self, response: httpx.Response) -> dict[str, Any]:
        """Parse JSON or raise a response error with details."""

        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as exc:
            self._logger.error("Malformed Binance response body", exc_info=True)
            raise BinanceResponseError(
                "Binance returned a malformed response.",
                status_code=response.status_code,
                details={"body": response.text},
            ) from exc

        if not isinstance(payload, dict):
            raise BinanceResponseError(
                "Binance response payload must be a JSON object.",
                status_code=response.status_code,
                details={"payload": payload},
            )

        return payload

    def _parse_error_response(self, response: httpx.Response) -> BinanceAPIError:
        """Convert a non-successful HTTP response into a domain error."""

        try:
            payload = response.json()
        except Exception:
            payload = {"msg": response.text}

        message = str(payload.get("msg") or f"HTTP {response.status_code}")
        code = payload.get("code")

        if response.status_code in {401, 403} or code in {-2015, -2014}:
            return BinanceAuthenticationError(
                message,
                code=_safe_int(code),
                status_code=response.status_code,
                details={"response": payload},
            )

        return BinanceAPIError(
            message,
            code=_safe_int(code),
            status_code=response.status_code,
            details={"response": payload},
        )

    @staticmethod
    def _default_time_provider() -> int:
        """Return the current epoch timestamp in milliseconds."""

        import time

        return int(time.time() * 1000)


def _safe_int(value: Any) -> int | None:
    """Best-effort conversion of Binance error codes to integers."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
