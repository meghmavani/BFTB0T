"""Shared domain models for trading requests and responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from .exceptions import BinanceResponseError


class OrderSide(StrEnum):
    """Supported order sides."""

    BUY = "BUY"
    SELL = "SELL"

    @classmethod
    def from_value(cls, value: str | OrderSide) -> OrderSide:
        """Normalize a user-provided side value."""

        if isinstance(value, cls):
            return value

        normalized = value.strip().upper()
        try:
            return cls[normalized]
        except KeyError as exc:
            raise ValueError(f"Invalid side: {value}") from exc


class OrderType(StrEnum):
    """Supported order types exposed by the CLI."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"

    @classmethod
    def from_value(cls, value: str | OrderType) -> OrderType:
        """Normalize a user-provided order type value."""

        if isinstance(value, cls):
            return value

        normalized = value.strip().upper().replace("-", "_").replace(" ", "_")
        aliases = {"STOPLIMIT": cls.STOP_LIMIT, "STOP_LIMIT": cls.STOP_LIMIT}
        if normalized in aliases:
            return aliases[normalized]

        try:
            return cls[normalized]
        except KeyError as exc:
            raise ValueError(f"Invalid order type: {value}") from exc

    @property
    def api_value(self) -> str:
        """Return the Binance API order type."""

        return "STOP" if self is OrderType.STOP_LIMIT else self.value

    @property
    def display_value(self) -> str:
        """Return the user-facing label."""

        return "STOP-LIMIT" if self is OrderType.STOP_LIMIT else self.value


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """Validated order input accepted by the service layer."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class OrderResult:
    """Structured representation of a Binance order response."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None
    stop_price: Decimal | None
    order_id: int
    status: str
    executed_quantity: Decimal
    average_price: Decimal
    raw_response: Mapping[str, Any] = field(repr=False, default_factory=dict)

    @classmethod
    def from_binance_response(
        cls,
        response: Mapping[str, Any],
        request: OrderRequest,
    ) -> OrderResult:
        """Parse a Binance order response into a typed result."""

        try:
            order_id = int(response["orderId"])
            status = str(response["status"])
            symbol = str(response.get("symbol", request.symbol))
            executed_quantity = Decimal(str(response.get("executedQty", "0")))
            average_price = cls._parse_average_price(response, executed_quantity)
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise BinanceResponseError(
                "Binance returned an unexpected order payload.",
                details={"response": dict(response)},
            ) from exc

        return cls(
            symbol=symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            order_id=order_id,
            status=status,
            executed_quantity=executed_quantity,
            average_price=average_price,
            raw_response=dict(response),
        )

    @staticmethod
    def _parse_average_price(
        response: Mapping[str, Any],
        executed_quantity: Decimal,
    ) -> Decimal:
        """Derive the average price from the response payload."""

        for candidate in (
            response.get("avgPrice"),
            response.get("price"),
            response.get("stopPrice"),
        ):
            if candidate not in (None, ""):
                return Decimal(str(candidate))

        cumulative_quote = response.get("cumQuote") or response.get(
            "cummulativeQuoteQty"
        )
        if cumulative_quote not in (None, "") and executed_quantity > 0:
            return Decimal(str(cumulative_quote)) / executed_quantity

        return Decimal("0")

    def display_rows(self) -> dict[str, str]:
        """Return the values that should be rendered in the CLI."""

        return {
            "Symbol": self.symbol,
            "Side": self.side.value,
            "Type": self.order_type.display_value,
            "Quantity": self._format_decimal(self.quantity),
            "Price": self._format_optional_decimal(self.price),
            "Stop Price": self._format_optional_decimal(self.stop_price),
            "Order ID": str(self.order_id),
            "Status": self.status,
            "Executed Quantity": self._format_decimal(self.executed_quantity),
            "Average Price": self._format_decimal(self.average_price),
        }

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        return format(value, "f")

    @classmethod
    def _format_optional_decimal(cls, value: Decimal | None) -> str:
        return "N/A" if value is None else cls._format_decimal(value)
