"""Validation helpers for trading requests."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .exceptions import ValidationError
from .models import OrderRequest, OrderSide, OrderType

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,15}USDT$")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a Binance Futures symbol."""

    normalized = symbol.strip().upper()
    if not normalized:
        raise ValidationError("Symbol is required.")
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValidationError(
            "Symbol must be an uppercase USDT perpetual symbol such as BTCUSDT.",
        )
    return normalized


def validate_side(side: str | OrderSide) -> OrderSide:
    """Validate the side and return the enum value."""

    try:
        return OrderSide.from_value(side)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def validate_order_type(order_type: str | OrderType) -> OrderType:
    """Validate the order type and return the enum value."""

    try:
        return OrderType.from_value(order_type)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def validate_quantity(quantity: object) -> Decimal:
    """Validate order quantity."""

    return _validate_positive_decimal(quantity, field_name="quantity")


def validate_price(price: object | None, order_type: OrderType) -> Decimal | None:
    """Validate optional price based on the order type."""

    if order_type is OrderType.MARKET:
        if price is not None:
            raise ValidationError("Price is not allowed for MARKET orders.")
        return None

    if order_type is OrderType.LIMIT:
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        return _validate_positive_decimal(price, field_name="price")

    if order_type is OrderType.STOP_LIMIT:
        if price is None:
            raise ValidationError("Price is required for STOP-LIMIT orders.")
        return _validate_positive_decimal(price, field_name="price")

    raise ValidationError(f"Unsupported order type: {order_type}")


def validate_stop_price(
    stop_price: object | None, order_type: OrderType
) -> Decimal | None:
    """Validate the stop price for stop-limit orders."""

    if order_type is not OrderType.STOP_LIMIT:
        if stop_price is not None:
            raise ValidationError("Stop price is only allowed for STOP-LIMIT orders.")
        return None

    if stop_price is None:
        raise ValidationError("Stop price is required for STOP-LIMIT orders.")

    return _validate_positive_decimal(stop_price, field_name="stop price")


def validate_order_inputs(
    symbol: str,
    side: str | OrderSide,
    order_type: str | OrderType,
    quantity: object,
    price: object | None = None,
    stop_price: object | None = None,
) -> OrderRequest:
    """Validate raw CLI inputs and return a normalized order request."""

    normalized_order_type = validate_order_type(order_type)
    normalized_symbol = validate_symbol(symbol)
    normalized_side = validate_side(side)
    normalized_quantity = validate_quantity(quantity)
    normalized_price = validate_price(price, normalized_order_type)
    normalized_stop_price = validate_stop_price(stop_price, normalized_order_type)

    return OrderRequest(
        symbol=normalized_symbol,
        side=normalized_side,
        order_type=normalized_order_type,
        quantity=normalized_quantity,
        price=normalized_price,
        stop_price=normalized_stop_price,
    )


def _validate_positive_decimal(value: object, field_name: str) -> Decimal:
    """Parse and validate a strictly positive decimal value."""

    if isinstance(value, bool):
        raise ValidationError(f"{field_name.capitalize()} must be a number.")

    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationError(
            f"{field_name.capitalize()} must be a valid number."
        ) from exc

    if decimal_value <= 0:
        raise ValidationError(f"{field_name.capitalize()} must be greater than zero.")

    return decimal_value
