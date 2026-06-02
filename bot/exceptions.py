"""Custom exceptions used throughout the trading bot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TradingBotError(Exception):
    """Base class for all trading bot errors."""


class ConfigurationError(TradingBotError):
    """Raised when configuration is missing or invalid."""


class ValidationError(TradingBotError):
    """Raised when user input fails validation."""


@dataclass(slots=True)
class BinanceAPIError(TradingBotError):
    """Raised when Binance returns a non-successful response."""

    message: str
    code: int | None = None
    status_code: int | None = None
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        if self.code is None:
            return self.message
        return f"{self.message} (code={self.code})"


class BinanceAuthenticationError(BinanceAPIError):
    """Raised when Binance rejects the API key or signature."""


class BinanceNetworkError(BinanceAPIError):
    """Raised when a transport-level network error occurs."""


class BinanceTimeoutError(BinanceNetworkError):
    """Raised when a request times out."""


class BinanceResponseError(BinanceAPIError):
    """Raised when Binance returns a malformed or unexpected payload."""


class OrderPlacementError(TradingBotError):
    """Raised when an order cannot be prepared or placed."""
