# Binance Futures Testnet Trading Bot

This repository contains a production-oriented Python trading bot for the Binance USDT-M Futures testnet. It supports MARKET, LIMIT, and STOP-LIMIT orders, validates input before any API call, logs requests and failures, and includes an offline automated test suite.

## Project Overview

The codebase is organized around explicit separation of concerns:

- CLI layer: `cli.py`
- Business logic layer: `bot/orders.py`
- Binance API layer: `bot/client.py`
- Validation layer: `bot/validators.py`
- Logging layer: `bot/logging_config.py`
- Configuration layer: `bot/config.py`

The implementation is designed so that order validation and payload generation can be tested independently from Binance connectivity.

## Features

- MARKET orders
- LIMIT orders
- STOP-LIMIT orders as a bonus order type
- BUY and SELL sides
- Interactive prompts when arguments are missing
- Confirmation before order submission
- Colored, human-friendly terminal output
- Structured logging to `logs/trading_bot.log`
- Offline unit, integration, and CLI tests
- Static analysis support with Black, Ruff, and MyPy

## Architecture Diagram

```text
user
  |
  v
cli.py  ->  bot/orders.py  ->  bot/validators.py
  |                    |
  |                    v
  |               bot/client.py  ->  Binance Futures Testnet
  |
  v
bot/logging_config.py  ->  logs/trading_bot.log
bot/config.py          ->  environment variables / .env.example
```

## Setup Instructions

1. Create a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env` and fill in your Binance testnet credentials.
4. Run the CLI.

## Virtual Environment Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_BASE_URL=https://testnet.binancefuture.com
BINANCE_RECV_WINDOW=5000
BINANCE_TIMEOUT_SECONDS=10.0
BINANCE_LOG_DIR=logs
```

Only `BINANCE_API_KEY` and `BINANCE_API_SECRET` are required. The remaining values have safe defaults.

## Running Examples

### Market Order Example

```bash
python cli.py place-order \
    --symbol BTCUSDT \
    --side BUY \
    --type MARKET \
    --quantity 0.001
```

### Limit Order Example

```bash
python cli.py place-order \
    --symbol BTCUSDT \
    --side SELL \
    --type LIMIT \
    --quantity 0.001 \
    --price 100000
```

### Stop-Limit Example

```bash
python cli.py place-order \
    --symbol BTCUSDT \
    --side SELL \
    --type STOP_LIMIT \
    --quantity 0.001 \
    --price 99500 \
    --stop-price 99600
```

## Logging Information

The application writes logs to `logs/trading_bot.log`.

Logged information includes:

- timestamp
- request details
- response details
- validation failures
- Binance API failures
- network failures and timeouts

Secrets are never logged. The file handler uses a rotating log file so the output remains manageable.

## Example Log Output

### MARKET order

```text
2026-06-02 12:00:00 | INFO     | trading_bot.client | Submitting order symbol=BTCUSDT side=BUY type=MARKET quantity=0.001
2026-06-02 12:00:00 | INFO     | trading_bot.client | Order accepted order_id=123456 status=FILLED executed_quantity=0.001 avg_price=65000
```

### LIMIT order

```text
2026-06-02 12:01:00 | INFO     | trading_bot.client | Submitting order symbol=BTCUSDT side=SELL type=LIMIT quantity=0.001
2026-06-02 12:01:00 | INFO     | trading_bot.client | Order accepted order_id=234567 status=NEW executed_quantity=0 avg_price=0
```

## Testing Instructions

Run the full suite:

```bash
pytest
```

Run coverage for the bot package:

```bash
pytest --cov=bot
```

Generate HTML coverage reports:

```bash
pytest --cov=bot --cov-report=html
```

Static analysis commands:

```bash
black .
ruff check .
mypy .
```

## Continuous Integration

This repository includes a minimal GitHub Actions workflow at `.github/workflows/ci.yml` that runs on push and pull requests. The workflow performs these checks on Ubuntu with Python 3.11:

- Installs dependencies from `requirements.txt`
- Runs `ruff` linting
- Runs `mypy` for the `bot` package
- Runs `pytest` with coverage

If any check fails the workflow will fail, ensuring PRs meet the static-analysis and test requirements.

## Assumptions

- The project targets the Binance Futures USDT-M testnet only.
- STOP-LIMIT is represented through the Binance `STOP` order type with `price` and `stopPrice` fields.
- `newOrderRespType=RESULT` is used so the response includes useful execution data.
- A `.env.example` file is provided; copy it to `.env` locally.

## Troubleshooting

- If the CLI reports a configuration error, verify that `.env` contains valid API credentials.
- If the API returns an authentication error, confirm that the testnet keys were created for the Binance Futures testnet.
- If requests time out, increase `BINANCE_TIMEOUT_SECONDS` or retry later.
- If validation fails, review the symbol, side, quantity, price, and stop price values before resubmitting.

## Review Notes

The repository includes a dedicated testing strategy document at `TESTING_STRATEGY.md` mapping every assignment requirement to automated coverage.