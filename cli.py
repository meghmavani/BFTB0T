"""Typer-based command line interface for Binance Futures testnet orders."""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.client import BinanceClient
from bot.config import AppConfig, load_config
from bot.exceptions import (
    BinanceAPIError,
    BinanceAuthenticationError,
    BinanceNetworkError,
    BinanceResponseError,
    BinanceTimeoutError,
    ConfigurationError,
    TradingBotError,
    ValidationError,
)
from bot.logging_config import configure_logging
from bot.orders import OrderService

app = typer.Typer(add_completion=False, help="Binance Futures testnet trading bot")
console = Console()


@app.callback()
def main_group() -> None:
    """Binance Futures testnet trading bot."""

    return None


def create_order_service(config: AppConfig) -> OrderService:
    """Build the order service with a configured Binance client."""

    logger = configure_logging(config.log_dir)
    client = BinanceClient(config=config, logger=logger)
    return OrderService(client=client, logger=logger)


@app.command("place-order")
def place_order(
    symbol: str | None = typer.Option(
        None, "--symbol", help="Trading symbol, for example BTCUSDT."
    ),
    side: str | None = typer.Option(None, "--side", help="BUY or SELL."),
    order_type: str | None = typer.Option(
        None, "--type", help="MARKET, LIMIT, or STOP_LIMIT."
    ),
    quantity: str | None = typer.Option(None, "--quantity", help="Order quantity."),
    price: str | None = typer.Option(
        None, "--price", help="Limit price for LIMIT or STOP_LIMIT orders."
    ),
    stop_price: str | None = typer.Option(
        None, "--stop-price", help="Stop price for STOP_LIMIT orders."
    ),
) -> None:
    """Place a Binance Futures testnet order."""

    try:
        load_dotenv(dotenv_path=Path(".env"), override=False)
        config = load_config()
        service = create_order_service(config)

        resolved_symbol = symbol or typer.prompt("Symbol", default="BTCUSDT")
        resolved_side = side or typer.prompt("Side", default="BUY")
        resolved_order_type = order_type or typer.prompt("Order type", default="MARKET")
        resolved_quantity = quantity or typer.prompt("Quantity", default="0.001")

        normalized_order_type = (
            resolved_order_type.strip().upper().replace("-", "_").replace(" ", "_")
        )
        if normalized_order_type in {"LIMIT", "STOP_LIMIT", "STOPLIMIT"}:
            resolved_price = price or typer.prompt("Price")
        else:
            resolved_price = price

        if normalized_order_type == "STOP_LIMIT":
            resolved_stop_price = stop_price or typer.prompt("Stop price")
        else:
            resolved_stop_price = stop_price

        if not typer.confirm("Place this order?"):
            console.print("[yellow]Order cancelled by user.[/yellow]")
            return

        result = service.place_order(
            symbol=resolved_symbol,
            side=resolved_side,
            order_type=resolved_order_type,
            quantity=resolved_quantity,
            price=resolved_price,
            stop_price=resolved_stop_price,
        )
        _render_success(result.display_rows())
    except ConfigurationError as exc:
        _render_failure(
            "Configuration error",
            str(exc),
            "Set BINANCE_API_KEY and BINANCE_API_SECRET in .env or the environment.",
        )
        raise typer.Exit(code=1) from exc
    except ValidationError as exc:
        _render_failure(
            "Validation error",
            str(exc),
            "Check symbol, side, type, quantity, price, and stop price values.",
        )
        raise typer.Exit(code=1) from exc
    except BinanceAuthenticationError as exc:
        _render_failure(
            "Authentication error",
            str(exc),
            "Verify the Binance testnet API key, secret, and signature.",
        )
        raise typer.Exit(code=1) from exc
    except BinanceTimeoutError as exc:
        _render_failure(
            "Network timeout",
            str(exc),
            "Retry the command or increase BINANCE_TIMEOUT_SECONDS.",
        )
        raise typer.Exit(code=1) from exc
    except BinanceNetworkError as exc:
        _render_failure(
            "Network failure",
            str(exc),
            "Check connectivity to https://testnet.binancefuture.com.",
        )
        raise typer.Exit(code=1) from exc
    except BinanceResponseError as exc:
        _render_failure(
            "Response error",
            str(exc),
            "Inspect the Binance testnet response schema and retry.",
        )
        raise typer.Exit(code=1) from exc
    except BinanceAPIError as exc:
        _render_failure(
            "Binance error",
            str(exc),
            "Review the error code and Binance futures testnet rules.",
        )
        raise typer.Exit(code=1) from exc
    except TradingBotError as exc:
        _render_failure(
            "Trading bot error",
            str(exc),
            "Review the command input and logs/trading_bot.log.",
        )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        _render_failure(
            "Unexpected error",
            str(exc),
            "Review logs/trading_bot.log for the full stack trace.",
        )
        raise typer.Exit(code=1) from exc


def _render_success(rows: dict[str, str]) -> None:
    """Render a successful order response."""

    summary = Table(title="ORDER SUMMARY", show_header=False, box=None)
    response = Table(title="ORDER RESPONSE", show_header=False, box=None)

    for label in ("Symbol", "Side", "Type", "Quantity", "Price"):
        summary.add_row(f"[bold cyan]{label}[/bold cyan]", rows.get(label, "N/A"))

    if rows.get("Stop Price") not in {None, "N/A"}:
        summary.add_row("[bold cyan]Stop Price[/bold cyan]", rows["Stop Price"])

    for label in ("Order ID", "Status", "Executed Quantity", "Average Price"):
        response.add_row(f"[bold cyan]{label}[/bold cyan]", rows.get(label, "N/A"))

    console.rule("ORDER SUMMARY", style="green")
    console.print(summary)
    console.print()
    console.rule("ORDER RESPONSE", style="green")
    console.print(response)


def _render_failure(reason: str, message: str, suggestion: str) -> None:
    """Render a user-friendly failure message."""

    panel = Panel.fit(
        f"[bold red]Reason:[/bold red] {message}\n\n"
        f"[bold yellow]Suggested Action:[/bold yellow] {suggestion}",
        title=reason,
        border_style="red",
    )
    console.print(panel)


def main() -> None:
    """Entry point used by `python cli.py`."""

    app()


if __name__ == "__main__":
    main()
