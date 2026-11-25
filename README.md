# Beyin Finance API Documentation

Public API documentation for [Beyin Finance](https://beyinfinance.com) trading platform.

Start with the [Quickstart](docs/quickstart.md). The
[strategy, backtest, and publishing guide](docs/strategy-backtest.md) covers
progress and recovery. See [Troubleshooting](docs/troubleshooting.md) for
authentication errors, rate limits, and uncertain request outcomes.

## Endpoints

| Route | Purpose |
|-------|---------|
| `POST /user?request_type=<type>` | Account, marketplace, strategy and signal operations |
| `GET /` | Public platform configuration |
| `GET /tradingdata?request_type=<type>` | Trend signals, public market data, bid/ask quotes |
| `POST /backtest?action=<action>` | Backtest estimates, jobs and results |
| `POST /ai?request_type=<type>` | Authenticated AI chat and market-analysis operations |
| `/education/v1/...` | Education catalog, learning and Leader Studio routes; commercial checkout remains configuration-dependent |

## Authentication

- **Developer API credentials:** `X-API-Key` + `X-API-Secret`
- **Public market data:** No credentials when explicitly stated in the endpoint reference

Create and revoke developer credentials from the Beyin Finance account
interface. The secret is shown only when a credential is created.

## Build the documentation locally

```bash
python -m pip install -r docs/requirements.txt
python -m unittest discover -s tests
python -m sphinx -E -W --keep-going -b html docs _build/html
python tests/check_rendered_links.py _build/html
```

## Hosted Docs

The published reference is at [docs.beyinfinance.com](https://docs.beyinfinance.com).
