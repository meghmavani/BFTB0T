"""Order payload generation and orchestration logic."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from .exceptions import ValidationError
from .models import OrderRequest, OrderResult, OrderType
from .validators import validate_order_inputs


def build_market_order_payload(request: OrderRequest) -> dict[str, str]:
    """Build a Binance payload for a market order."""

    return _base_payload(request, order_type=request.order_type.api_value)


def build_limit_order_payload(request: OrderRequest) -> dict[str, str]:
    """Build a Binance payload for a limit order."""

    if request.price is None:
        raise ValidationError("Price is required for LIMIT orders.")

    payload = _base_payload(request, order_type=request.order_type.api_value)
    payload.update({"timeInForce": "GTC", "price": _format_decimal(request.price)})
    return payload


def build_stop_limit_order_payload(request: OrderRequest) -> dict[str, str]:
    """Build a Binance payload for a stop-limit order."""

    if request.price is None:
        raise ValidationError("Price is required for STOP-LIMIT orders.")
    if request.stop_price is None:
        raise ValidationError("Stop price is required for STOP-LIMIT orders.")

    payload = _base_payload(request, order_type=request.order_type.api_value)
    payload.update(
        {
            "timeInForce": "GTC",
            "price": _format_decimal(request.price),
            "stopPrice": _format_decimal(request.stop_price),
        }
    )
    return payload


def build_order_payload(request: OrderRequest) -> dict[str, str]:
    """Dispatch to the correct payload builder for the request."""

    if request.order_type is OrderType.MARKET:
        return build_market_order_payload(request)
    if request.order_type is OrderType.LIMIT:
        return build_limit_order_payload(request)
    if request.order_type is OrderType.STOP_LIMIT:
        return build_stop_limit_order_payload(request)

    raise ValidationError(f"Unsupported order type: {request.order_type}")


class OrderService:
    """Business logic for validating, building, and submitting orders."""

    def __init__(self, client: Any, logger: logging.Logger | None = None) -> None:
        self._client = client
        self._logger = logger or logging.getLogger("trading_bot.order_service")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: object,
        price: object | None = None,
        stop_price: object | None = None,
    ) -> OrderResult:
        """Validate an order and send it to Binance through the client."""

        try:
            request = validate_order_inputs(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )
        except ValidationError:
            self._logger.warning(
                "Validation failed for order request symbol=%s side=%s type=%s quantity=%s",
                symbol,
                side,
                order_type,
                quantity,
                exc_info=True,
            )
            raise

        payload = build_order_payload(request)
        self._logger.info(
            "Prepared order request symbol=%s side=%s type=%s quantity=%s",
            request.symbol,
            request.side.value,
            request.order_type.display_value,
            _format_decimal(request.quantity),
        )
        return self._client.place_order(request, payload)


def _base_payload(request: OrderRequest, order_type: str) -> dict[str, str]:
    """Build the common Binance payload shared by all order types."""

    return {
        "symbol": request.symbol,
        "side": request.side.value,
        "type": order_type,
        "quantity": _format_decimal(request.quantity),
        "newOrderRespType": "RESULT",
    }


def _format_decimal(value: Decimal) -> str:
    """Format a decimal without scientific notation."""

    formatted = format(value, "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
