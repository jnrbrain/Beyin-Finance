# Beyin Finance API Documentation

Public API documentation for [Beyin Finance](https://beyinfinance.com) trading platform.

## Endpoints

| Route | Purpose |
|-------|---------|
| `POST /user?request_type=<type>` | Account, marketplace, strategy and signal operations |
| `GET /` | Public platform configuration |
| `GET /tradingdata?request_type=<type>` | Trend signals, public market data, bid/ask quotes |
| `POST /backtest?action=<action>` | Backtest estimates, jobs and results |

## Authentication

- **Developer API credentials:** `X-API-Key` + `X-API-Secret`
- **Public market data:** No credentials when explicitly stated in the endpoint reference

Create and revoke developer credentials from the Beyin Finance account
interface. The secret is shown only when a credential is created.

## Build the documentation locally

```bash
pip install -r docs/requirements.txt
cd docs && make html
```

## Hosted Docs

Deployed via ReadTheDocs at the configured URL.
