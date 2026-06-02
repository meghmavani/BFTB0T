"""Shared test fixtures and sample payloads."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from bot.config import AppConfig
from bot.models import OrderRequest, OrderResult, OrderSide, OrderType

TEST_CONFIG = AppConfig(
    api_key="test-api-key",
    api_secret="test-api-secret",
    base_url="https://testnet.binancefuture.com",
    recv_window=5000,
    timeout_seconds=10.0,
    log_dir=Path("logs"),
)

MARKET_REQUEST = OrderRequest(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal("0.001"),
)

LIMIT_REQUEST = OrderRequest(
    symbol="BTCUSDT",
    side=OrderSide.SELL,
    order_type=OrderType.LIMIT,
    quantity=Decimal("0.001"),
    price=Decimal("100000"),
)

STOP_LIMIT_REQUEST = OrderRequest(
    symbol="BTCUSDT",
    side=OrderSide.SELL,
    order_type=OrderType.STOP_LIMIT,
    quantity=Decimal("0.001"),
    price=Decimal("99500"),
    stop_price=Decimal("99600"),
)

MARKET_RESPONSE = {
    "symbol": "BTCUSDT",
    "orderId": 123456,
    "status": "FILLED",
    "executedQty": "0.001",
    "avgPrice": "65000",
    "type": "MARKET",
}

LIMIT_RESPONSE = {
    "symbol": "BTCUSDT",
    "orderId": 234567,
    "status": "NEW",
    "executedQty": "0",
    "avgPrice": "0",
    "type": "LIMIT",
}

STOP_LIMIT_RESPONSE = {
    "symbol": "BTCUSDT",
    "orderId": 345678,
    "status": "NEW",
    "executedQty": "0",
    "avgPrice": "0",
    "type": "STOP",
}

API_ERROR_RESPONSE = {"code": -2010, "msg": "Order would immediately trigger."}
AUTH_ERROR_RESPONSE = {
    "code": -2015,
    "msg": "Invalid API-key, IP, or permissions for action.",
}

RESULT = OrderResult(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal("0.001"),
    price=None,
    stop_price=None,
    order_id=123456,
    status="FILLED",
    executed_quantity=Decimal("0.001"),
    average_price=Decimal("65000"),
)
