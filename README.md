# Beyin Finance API Documentation

Public API documentation for [Beyin Finance](https://beyinfinance.com) trading platform.

## Architecture

```
Client (Flutter/Web) → API Gateway → AWS Lambda (BeyinFinanceUserAPI)
                                   → Lightsail Proxy → Binance API (signed)
```

## Endpoints

| Route | Purpose |
|-------|---------|
| `POST /user?request_type=<type>` | All user/marketplace/signal operations |
| `GET /` | Platform configuration (plans, metrics) |
| `GET /tradingdata?request_type=<type>` | Trend signals, market sentiment |
| `POST /beyinai` | AI strategy generation |

## Authentication

- **JWT**: 3-day session token, obtained via `login`
- **API Key**: `X-API-Key` + `X-API-Secret` headers for programmatic access

## Local Development

```bash
pip install -r docs/requirements.txt
cd docs && make html
```

## Hosted Docs

Deployed via ReadTheDocs at the configured URL.
