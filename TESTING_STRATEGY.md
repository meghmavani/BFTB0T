# Testing Strategy

This project includes unit, integration, and CLI tests designed to validate core behaviors without contacting the real Binance API.

- Unit tests: located under `tests/unit` and exercise parsing, validation, and small helpers.
- Integration tests: located under `tests/integration` and use `respx` to mock HTTP requests and validate signing and request composition.
- CLI tests: located under `tests/cli` and exercise the Typer command flow using the Click `CliRunner`.

How to run:

```bash
pytest
pytest --cov=bot
```

Notes:
- Tests mock network I/O; you do not need Binance credentials to run the test suite.
- To run a single test file: `pytest tests/unit/test_client.py -q`.