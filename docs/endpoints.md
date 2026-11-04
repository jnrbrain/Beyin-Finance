# Beyin Finance Developer API Reference

**Base URL:** `https://api.beyinfinance.com`

All endpoints in this reference are relative to this base URL (for example,
`POST https://api.beyinfinance.com/user?request_type=account_info`).

---

## Authentication

Use the Developer API credential pair on authenticated endpoint operations that
support integrator authentication. Authentication is endpoint-specific; this
pair is not a replacement for first-party sessions or provider webhook proofs.

| Request surface | Authentication |
|--------|----------------|
| Supported authenticated REST operations on `/user`, `/tradingdata`, `/backtest`, and `/ai` | `X-API-Key` + `X-API-Secret` |
| Guest-read routes explicitly marked below | No credential required |
| JWT-only, payment-provider, webhook, Education-internal, and WebSocket flows | Their endpoint-specific credential; Developer API keys do not replace it |

This does **not** mean one Developer API key works on every route in the API.
Use it only on operations documented as accepting integrator authentication:
the supported operations under `/user` and `/tradingdata`, plus `/backtest`
and `/ai`. `/user` has request-type-specific exceptions; key creation/revocation
and session administration require a first-party session (key status accepts
the current key), and login,
registration, deletion, payment callbacks, Education-internal operations, and
the community WebSocket use their own authentication flow. A public guest route
does not need an API key, but if you send a key pair and it is invalid the API
returns 401 instead of silently treating the request as a guest.

**Developer API-key example:**

```
X-API-Key: bf_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
X-API-Secret: bf_sec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

Generate API keys from the Telegram bot, web dashboard, or mobile app.

A missing or invalid credential returns HTTP 401 on authenticated routes.
`/user` and `/backtest` operations require a tracked caller identity; selected
`/tradingdata` and `/` routes are guest-accessible as marked below.
Developer API-key `permissions` values are metadata today; route access is
determined by the endpoint's authentication rules, not by that field.

Developer API keys work only where the operation accepts integrator
authentication. They do not authorize first-party login/registration, JWT-only
administrative or session actions, payment receipts and provider callbacks, or
the community WebSocket connection flow. `/user` request types retain their
individual auth requirements; follow the endpoint-specific notes below.

For a Developer API request to `/backtest`, send the two API-key headers without
the first-party `jwt_token` or `auth_type: jwt` headers. The mobile app uses JWT
for its backtest flow. A `session_revoked` response means that app session is no
longer active; an invalid Developer API key uses `invalid_credentials`.

### Binance request routing

All client and developer calls use the single REST origin
`https://api.beyinfinance.com/` and the documented `/user` routes. The
application server sends Binance-signed private requests from Beyin Finance's
Binance egress address. When IP restriction is enabled, Binance API keys used
with Beyin Finance must allow `3.120.214.198`.

> **Scope — first-party authentication flows are not a public integrator surface.**
> The first-party sign-in and account-linking flows — login, registration,
> Google linking, and Telegram linking — are owned by the official Beyin Finance
> clients (mobile app, web, Telegram bot) and are intentionally **not documented
> as public integrator endpoints**. Their absence from this reference is by
> design, not an omission. Integrators authenticate with Developer API
> credentials (`X-API-Key` + `X-API-Secret`), not by driving the first-party
> login/registration flows.

> **Note:** Some read-only Trading Data endpoints allow guest access. Requests
> remain subject to service-level protections, and guest access does not
> guarantee availability or throughput. The guest routes are `trend_signals`,
> `trend_signal_detail`, `trend_indicator`, `trend_indicator_history`,
> `sentiment_breakout_signals`, `market_ticker`, `market_live`,
> `market_candles`, `get_klines`, `market_quote`, `market_symbol_info`,
> `platform_notifications`, `community_posts`, `community_chat`,
> `community_leaders`, `marketplace_browse`, `marketplace_listing`,
> `marketplace_reviews`, and `changelog`.

A rejected or revoked Developer API key carries `"code":
"invalid_credentials"`. See the Errors section for the complete marker table.

If credentials cannot be evaluated because a required service is temporarily
unavailable, the request returns HTTP 503 with
`"code": "api_key_store_unavailable"`. That is an outage to retry, not a
credential to replace.

### Telegram Bot Scope

The Telegram bot is an account handoff and notification channel. It can create
or link a Beyin Finance account, show account and plan information, deliver
signals, manage signal automation preferences, and guide manually confirmed
Binance order actions. It is not a separate market-data source, and clients must
still use the Beyin Finance API endpoints documented here.

### Request correlation

A **correlation ID** is a short identifier you attach to a request so you can
trace it end-to-end — in your own logs and when reporting an issue to support.
Send one logical ID per operation and reuse the *same* value across automatic
retries of that operation, so a retried request is recognisable as the same
logical call rather than a new one.

Send it in the `X-Correlation-ID` request header. The value must be **8–128
characters** and may contain only letters, digits, and the characters
`.` `_` `:` `-`. If you send an invalid or empty value, the API ignores it and
generates its own ID (prefixed `bf-`) so a correlation ID is always present.

The accepted (or generated) value is echoed back in the `X-Correlation-ID`
response header, and it is listed in `Access-Control-Expose-Headers` so
browser-based clients can read it.

**Request:**

```
POST /user?request_type=account_info
X-Correlation-ID: acct-load-2f9a1c7e
```

**Response headers:**

```
X-Correlation-ID: acct-load-2f9a1c7e
Access-Control-Expose-Headers: X-Correlation-ID,X-RateLimit-Limit,X-RateLimit-Remaining,X-RateLimit-Reset
```

If you had sent `X-Correlation-ID: ab` (too short) or omitted the header, the
response would instead carry a server-generated value such as
`X-Correlation-ID: bf-17c3f9a1b2d4e5f6`.

---

## Rate Limits

Application rate limits vary by route and account. `/user` returns the
authenticated account's current limit after its identity has been resolved;
other surfaces may use their own rules. If a response includes the headers
below, use those values for that request. Limits may change; response headers
are authoritative for the current request.

### Rate Limit Headers

Responses from routes with an application rate counter include:

```
X-RateLimit-Limit: 60         # Current route/account limit
X-RateLimit-Remaining: 47     # Requests remaining in the current window
X-RateLimit-Reset: 1784990340 # Unix timestamp when the window resets
```

When rate limited (HTTP 429):
```
Retry-After: 15               # Seconds until reset
```

### Plan Limits

| Plan | Monthly | Annual (-50%) | Max Active Strategies | Max Pairs/Strategy |
|------|---------|---------------|----------------------|-------------------|
| Free | – | – | 0 | 0 |
| Starter | $10 | $60 | 1 | 1 |
| Plus | $20 | $120 | 2 | 5 |
| Pro | $50 | $300 | 5 | 10 |
| Investor | $100 | $600 | 10 | 20 |

### Payment

Payment behavior depends on the channel:

- **Shopier card purchases are one-time purchases.** They extend your plan for
  the purchased period and do **not** renew automatically. When the period
  ends, you must make another Shopier purchase to keep the plan active.
- **iOS and Android plan purchases are store subscriptions.** They renew
  automatically through the App Store or Google Play until you cancel them in
  the relevant store. Store renewals extend the plan without a new Shopier
  order.

Every purchase must be tied to your account by your **6-character Beyin ID**
(for example `MTHG7A`), which you can find in your profile / account info.

#### Card payment — Shopier

Pay by card through the Beyin Finance Shopier store:

- **Store:** <https://www.shopier.com/beyinfinance>
- Open the store, pick the listing for the plan and period you want, and
  complete checkout. Each plan and billing period has its own listing.
- **Important:** during checkout, type your **6-character Beyin ID** into the
  order note field. This is how the payment is matched to your account. If you
  are unsure the note was saved, keep your order email so support can match it
  by e-mail as a fallback.

#### Crypto — Binance Pay (currently suspended)

> **Notice — crypto payments are suspended.** In line with applicable SPK
> requirements and our current compliance policy, crypto payment purchases are
> currently suspended. **Do not send payment through Binance Pay.** This is an
> operational notice for Beyin Finance and is not legal advice. See the
> [SPK crypto-asset service provider notice](https://spk.gov.tr/duyurular/basin-duyurulari/2025/kripto-varlik-hizmet-saglayicilarina-iliskin-iki-tebli%C4%9F-yayimlandi)
> for the applicable regulatory framework.

> Binance Pay support is retained as a configured fallback if other payment
> providers are unavailable. It is shown only when payment configuration and
> the current compliance policy allow it. While the suspension notice above is
> active, do not send a payment.

For historical reference only (not a payment instruction):

- **Binance Account ID:** `863 826 81`

#### Mobile — in-app subscriptions

In the iOS and Android apps, plan purchases are store-managed subscriptions:

- **Android:** Google Play Billing. **iOS:** Apple In-App Purchase (StoreKit).
- Products are the plan × period SKUs (`beyin_<plan>_monthly` /
  `beyin_<plan>_annual`); a single education product is sold as a one-time
  purchase.
- Your Beyin ID is bound to the purchase automatically by the app, so there is
  no note to fill in. Every purchase is **verified server-side** with the store
  before your plan is granted — the app does not unlock a plan on the device
  alone.
- Plan subscriptions **auto-renew** through the App Store / Google Play until
  you cancel them in the store. Renewals and refunds are applied to your Beyin
  Finance plan automatically. The education product is the exception: it is a
  one-time purchase and is not a recurring subscription.

### Client Best Practices

- Read `X-RateLimit-Remaining` from every response
- If `Remaining` < 5, slow down or delay requests
- On 429, wait `Retry-After` seconds before retrying
- Cache responses when possible (e.g. `account_info`, `available_coins`)

### Backtest Job Status Response Schema

`POST /backtest?action=status`

```json
{
  "action": "status",
  "job_id": "job_1784990340",
  "status": "running",
  "progress_pct": 45,
  "coin_progress": {
    "BTC": {"status": "running", "progress_pct": 45},
    "ETH": {"status": "queued", "progress_pct": 0}
  },
  "active_coins": ["BTC"],
  "queued_coins": ["ETH"],
  "max_active_coins_per_user": 2
}
```

When a request exceeds the current limit, the API returns HTTP 429 with a
`Retry-After` header:

**Rate Limit Response (HTTP 429):**
```json
{
  "error": "Too many requests. Please wait before trying again.",
  "reason": "rate_limit_exceeded",
  "retry_after": 15
}
```

**Service Temporarily Unavailable (HTTP 503):**

When a required service is temporarily unavailable, a request may return HTTP
503. Use the response's retry delay and the normal idempotency guidance for
state-changing requests:

```json
{
  "error": "Service temporarily unavailable; please retry shortly",
  "reason": "temporarily_unavailable",
  "retry_after": 5
}
```

### Common `reason` codes
- `rate_limit_exceeded` (HTTP 429): Your per-minute request limit was exceeded.
- `temporarily_unavailable` (HTTP 503): The request cannot be processed right
  now; retry after the indicated delay.
- `backtest_concurrency_limit` (HTTP 429): A backtest launch cannot be accepted
  while the account is at its current launch limit. Follow `Retry-After` before
  trying again. The response may include account-level `current_running` and
  `max_concurrent` counts.
- `strategy_generation_in_progress` (HTTP 429): You already have the maximum
  number of AI strategy generations running
  (`/user?request_type=strategy_generate`).
  Wait for the current generation to finish and follow `Retry-After` before
  trying again. The response includes `max_concurrent`.
- `backtest_capacity_exceeded` (HTTP 429): The request cannot be accepted right
  now. Retry after the indicated delay.

**Recommended Handling:**
Inspect the `Retry-After` header (or the `retry_after` JSON field, in seconds)
and apply exponential backoff with random jitter before retrying.

> These `reason` codes and the `Retry-After` / `retry_after` contract apply to
> the request-facing REST endpoints (the User API and backtest API). Real-time
> WebSocket channels signal overload with a plain `429` close/response without a
> `Retry-After` value — back off client-side when you see one.

---

## Account

### Get Account Info

`POST /user?request_type=account_info`

No body required.

**Response:**
```json
{
  "ok": true,
  "data": {
    "beyin_id": "MTHG7A",
    "plan": "pro",
    "beyin_credits": 7.35,
    "license_expires_at": 1790000000,
    "demo_expires_at": 0,
    "active_own_strategies": 3,
    "community_role": "leader",
    "connections": {
      "binance": true,
      "telegram": false,
      "google": true
    },
    "notification_settings": {
      "app": true,
      "announcement": true,
      "account": true,
      "bot": true,
      "telegram": false,
      "mail": false
    },
    "referral": {
      "code": "BF-REF-123",
      "commissions": [
        {
          "commission_id": "payment-1",
          "amount_usdt": 1.25,
          "status": "recorded"
        }
      ],
      "total_commission_usdt": 1.25
    },
    "strategies": {
      "emacross": {
        "name": "emacross",
        "status": "active",
        "candle_count": 32,
        "direction_agnostic": true,
        "signal_mode": "signal_orders",
        "version": 1,
        "visibility": "private"
      }
    }
  }
}
```

Connection values are booleans only. Referral entries use the documented
identifier, amount and status fields.

### Get Login History

`POST /user?request_type=login_history`

Returns recent login activity for the authenticated account, newest first. Use
this endpoint to review account access activity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

```json
{
  "ok": true,
  "data": {
    "logins": [
      {
        "login_id": "login#abc...",
        "ip_address": "192.0.2.10",
        "platform": "android",
        "login_at": 1784936800
      }
    ],
    "count": 1,
    "last_evaluated_key": "base64...",
    "has_more": true
  }
}
```

`login_id` is the stable duplicate-removal key. Return the opaque cursor
unchanged; malformed cursors and non-integer page sizes return HTTP 400.

### Get Credits History

`POST /user?request_type=credits_history`

Returns signed credit movements from all available monthly logs and deposits,
newest first. Positive `amount` values add credits; negative values consume
credits.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 50, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{
  "ok": true,
  "data": {
    "transactions": [
      {"transaction_id": "credit#abc...", "type": "adjustment", "amount": 0.05, "action": "credit_adjustment", "description": "Credit adjustment", "timestamp": 1784936800},
      {"transaction_id": "credit#def...", "type": "spend", "amount": -0.01, "action": "economic_news", "description": "Economic news fetch", "timestamp": 1784936700},
      {"transaction_id": "credit#telegram-reward", "type": "credit", "amount": 0.5, "action": "telegram_link_reward", "description": "Telegram bağlantı ödülü (+0.5 kredi)", "timestamp": 1784936900},
      {"transaction_id": "deposit#payment-1", "type": "deposit", "amount": 5.0, "action": "deposit", "description": "Payment abc12345", "timestamp": 1784900000}
    ],
    "count": 3,
    "last_evaluated_key": "base64...",
    "has_more": true
  }
}
```

**Transaction actions:** `deposit`, `backtest`, `credit_adjustment`, `strategy_generate`, `strategy_refund`, `marketplace_signal`, `telegram_link_reward`, `google_link_reward`, `binance_link_reward`

Telegram registration and the first Telegram link to an existing account grant a
one-time `0.5` credit reward. The reward is idempotent per Telegram account and
appears as a positive `telegram_link_reward` transaction in this history.

Automatic recovery details and adjustment reasons are not exposed through the
customer API. Clients should display `credit_adjustment` as a generic balance
correction and rely on the signed `amount`.

The deterministic `transaction_id` is the duplicate-removal key. Return the
opaque cursor unchanged; malformed cursors and non-integer page sizes return
HTTP 400.

### Get Binance Balance

`POST /user?request_type=binance_balance`

Requires Binance API keys linked. No body params.

**Response:**
```json
{
  "ok": true,
  "data": {
    "spot": {"BTC": 0.001, "USDT": 250.0},
    "futures": {"USDT": 100.0},
    "funding": {"USDT": 50.0}
  }
}
```

### Get Order History

`POST /user?request_type=order_history`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | No | `"active"` (default) returns open/entered signals; `"closed"` returns closed orders |
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

Records are ordered newest first. This is Beyin Finance's tracked order history,
not a complete copy of every order in the Binance account. `order_history_id` is
the stable account-scoped identifier used by `binance_order_cancel`. Return the
opaque cursor unchanged; malformed cursors, invalid statuses and non-integer
page sizes return HTTP 400. Undocumented fields and stored exchange/credential
payloads are removed from the response.

**Response:**
```json
{
  "ok": true,
  "data": {
    "orders": [
      {
        "order_id": "ord_1784936800",
        "record_type": "oco_order",
        "order_history_id": "order#12345678",
        "timestamp": 1784936800,
        "strategy_name": "emacross",
        "coin": "BTC",
        "symbol": "BTCUSDT",
        "exchange_order_status": "NEW",
        "execution_mode": "real_trade",
        "order_source": "signal",
        "signal_position_key": "pos_1784850000",
        "oco_order_list_id": "12345678",
        "take_profit_price": "67000.00",
        "stop_loss_price": "63000.00"
      }
    ],
    "count": 1,
    "status": "active",
    "last_evaluated_key": "base64...",
    "has_more": true
  }
}
```

### Preview Binance OCO Order

`POST /user?request_type=binance_order_preview`

Uses the same business fields as `binance_order`, but does **not** place an
exchange order or reserve balance. The API reads current Binance Spot symbol
filters, rounds quantity to an increment valid for both limit and market legs,
rounds prices to the price tick, validates minimums and checks the linked
account's available base-asset balance. Placement is supported for **Spot
long exits only**. A successful preview is not a balance reservation;
execution repeats validation because market, filters and account balances can
change.

**Response:**
```json
{
  "ok": true,
  "data": {
    "symbol": "BTCUSDT",
    "position_side": "BUY",
    "order_side": "SELL",
    "quantity": "0.001",
    "take_profit_price": "67000.00",
    "stop_loss_price": "63000.00",
    "price_precision": 2,
    "quantity_precision": 3,
    "minimum_notional": "5",
    "minimum_quantity": "0.00001",
    "maximum_quantity": "9000",
    "price_tick_size": "0.01",
    "quantity_step_size": "0.00001",
    "stop_loss_execution": "market",
    "balance_asset": "BTC",
    "available_balance": "0.010",
    "required_balance": "0.001",
    "balance_verified": true,
    "market_type": "spot",
    "leverage": 1,
    "order_source": "signal",
    "signal_position_key": "pos_1784850000",
    "irreversible": true
  }
}
```

`position_side` is the user's position direction (`BUY` means a long Spot
holding); `order_side` is the actual Binance order side (`SELL`). This endpoint
does not create an entry buy. It attaches exits to an existing Spot balance.
`stop_loss_price` is a trigger price; after it triggers, a market sell executes
at the available price and can slip. The TP leg is a `LIMIT_MAKER` sell at
`take_profit_price`. Binance may reject a TP price that would immediately take
liquidity.

`market_type` is always `"spot"` and `leverage` is always `1`; Futures order
placement is not permitted. The preview returns actual normalized values and
the filter increments used. Clients should show those returned values in the
confirmation step rather than relying on locally rounded inputs.

`idempotency_key` is required for placement, not for preview. If the client
creates it before preview, it must reuse it for the matching placement and all
retries. Use the same `quantity`, TP and SL values from the preview response.

The client must obtain a successful preview and require explicit user
confirmation before calling `binance_order`.

### Place Binance OCO Order

`POST /user?request_type=binance_order`

Places a Spot OCO (One-Cancels-Other) exit on Binance for an existing long
balance. The TP leg is a `LIMIT_MAKER` sell. The SL leg is a `STOP_LOSS`
market sell: `stop_loss_price` triggers the sale, but the final fill price is
not guaranteed and may be lower during fast markets. Binance cancels the other
leg when one leg completes. The implementation uses Binance's current
`POST /api/v3/orderList/oco` route: `aboveType=LIMIT_MAKER` with
`abovePrice` for take-profit, and `belowType=STOP_LOSS` with
`belowStopPrice` for the stop trigger. It does not send a stop-limit price or
time-in-force because the stop leg is a market order. See Binance's
[Spot REST API reference](https://developers.binance.com/en/docs/products/spot/rest-api).

Requires Binance API keys linked.

:::{important}
Before using this endpoint, the user's Binance API key must allow Spot trading and account/balance reads. Keep withdrawals disabled. If the key is IP-restricted, allow the current Beyin Finance Binance egress address:

`3.120.214.198`

Binance may reject signed requests if this address is not included in the key's IP allowlist.
:::

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | e.g. `"BTCUSDT"` |
| `side` | string | Yes | Position direction. Spot long exits require `"BUY"`; `"SELL"` short positions are not supported |
| `quantity` | string | Yes | Base-asset amount to sell. Preview normalizes this to the Binance Spot limit and market quantity increments |
| `entry_price` | string | No | Optional reference price recorded with the order; it does not submit an entry order |
| `take_profit_price` | string | Yes | TP limit-sell price. Preview normalizes it to the symbol's price tick |
| `stop_loss_price` | string | Yes | SL market-sell trigger price. It is not a guaranteed execution price |
| `market_type` | string | No | Must be `"spot"` (default). `"futures"` is rejected with HTTP 403 — futures order placement is prohibited (see note below). |
| `order_source` | string | Yes | `"signal"` when entering an active Signal + Orders signal; `"independent"` for an order not linked to a signal |
| `signal_position_key` | string | Conditional | Opaque signal position key required for `order_source=signal`; forbidden for independent orders |
| `idempotency_key` | string | Yes | 16-128 letters, numbers, `_` or `-`; reuse the same key for retries of the same order |

:::{warning}
Send decimal values as strings. Price decimal-place counts alone do not capture
increments such as `0.05`; the preview rounds to and returns the actual
`price_tick_size` and `quantity_step_size` values used.
:::

:::{note}
- The preview reports the normalized prices, quantity, minimums, tick size and quantity increment. Confirm the values that the API will actually submit.
- During preview and immediately before a real submission, the API validates
  account balance and order constraints again.
- The same idempotency key must be reused for retries of the same logical order.
- For `order_source=signal`, provide the opaque `signal_position_key` returned
  by the signal endpoint.
- Spot OCO is an exit for an existing base-asset balance. It does not buy the
  coin or create a short position.
- The stop-loss is a market sell after its trigger. Price gaps and low liquidity
  can cause slippage; the trigger price is not a guaranteed fill price.
:::

:::{warning}
**Futures order placement is not available.** Futures market data and
backtesting remain separate capabilities; live OCO submission accepts Spot
only and rejects `market_type="futures"` with HTTP 403.
:::

**Example body:**
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "0.001",
  "entry_price": "65000.00",
  "take_profit_price": "67000.00",
  "stop_loss_price": "63000.00",
  "market_type": "spot",
  "order_source": "signal",
  "signal_position_key": "pos_1784850000",
  "idempotency_key": "idem_1784990000"
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "order_list_id": "12345678",
    "client_order_id": "exchange_client_order_id",
    "symbol": "BTCUSDT",
    "side": "SELL",
    "quantity": "0.00100",
    "take_profit_price": "67000.00",
    "stop_loss_price": "63000.00",
    "take_profit_order_type": "LIMIT_MAKER",
    "stop_loss_execution": "market",
    "orders": [
      {"symbol": "BTCUSDT", "orderId": 111, "type": "LIMIT_MAKER"},
      {"symbol": "BTCUSDT", "orderId": 222, "type": "STOP_LOSS"}
    ],
    "signal_position_key": "pos_1784850000",
    "order_source": "signal",
    "idempotency_key": "idem_1784990000",
    "status": "submitted"
  }
}
```

Repeating the same idempotency key for the same logical order returns the
stored response with `idempotent_replay=true`.

```json
{"ok": true, "data": {"status": "processing", "idempotency_key": "idem_1784990000", "message": "Order submission is being verified."}}
```

If Binance definitively rejects the request, the API returns an actionable
error and remembers the idempotency result. If the same key is still being
processed, the API returns HTTP 202 with `status: "processing"`. If the
exchange response is ambiguous (for example, a timeout or server error after
submission), the API first queries Binance using the same OCO client order ID.
A recovered order is returned as submitted. If the result still cannot be
verified, it returns HTTP 202 with `status: "unknown_checking"`. For either
pending state, the client must keep the same key and must not submit a
duplicate. Refresh `order_history` before taking another action.

**Errors:**
- 400: Invalid fields, unsupported Spot short direction, invalid source/link combination, invalid idempotency key, insufficient balance, or a locally detected filter/minimum violation
- 403: Futures submission or Binance credential/permission rejection
- 404: A linked active signal does not exist for the authenticated user
- 409: The key was reused with a different order, or the linked signal does not match the symbol
- 422: Binance definitively rejected the order or its exchange-side order filters failed
- 429: Binance rate limit; `retry_after` may be present
- 503: Filters, balance or a required service could not be verified; the order was not submitted
- 202: Submission is still processing or its outcome is ambiguous; check `order_history` and do not duplicate the order

### Cancel Binance OCO Order

`POST /user?request_type=binance_order_cancel`

Cancels an active Spot OCO order that belongs to the authenticated account. The
API verifies the `order_history_id` against Beyin Finance's stored order record,
checks the current Binance order-list state, and then requests cancellation.
If a TP or SL leg completes first, the API reports that the order is already
closed instead of claiming it was cancelled. A timeout is reconciled against
Binance before a final result is returned.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | USDT Spot pair, e.g. `"BTCUSDT"` |
| `order_history_id` | string | Yes | Account-scoped ID returned by `order_history` |

**Example body:**
```json
{"symbol": "BTCUSDT", "order_history_id": "order#12345678"}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "status": "cancelled",
    "cancelled": true,
    "exchange_status": "ALL_DONE",
    "order_history_id": "order#12345678",
    "order_list_id": "12345678",
    "symbol": "BTCUSDT",
    "local_status_synced": true
  }
}
```

`status` can be `cancelled`, `already_closed`, `already_filled`, or
`unknown_checking`. For `unknown_checking` (HTTP 202), refresh `order_history`
before retrying. HTTP 404 means no matching account-owned active Spot OCO was
found; HTTP 409 means the stored record cannot be cancelled as a Spot OCO.

### Get Notifications

`POST /user?request_type=notifications_list`

Returns personal notifications newest first.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 50, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{
  "ok": true,
  "data": {
    "notifications": [
      {"id": "notification_1784900000", "title": "Backtest Complete", "body": "Your BTC 4h backtest finished", "event_type": "backtest_complete", "timestamp": 1784900000}
    ],
    "count": 1,
    "last_evaluated_key": "base64...",
    "has_more": true
  }
}
```

The cursor encodes the last `(timestamp, id)` ordering key and must be returned
unchanged. `has_more=false` with a null cursor is the final page. A malformed
cursor or non-integer page size returns HTTP 400.

### Mark Notifications Read

`POST /user?request_type=notifications_mark_read`

Mark one notification:

```json
{"notification_id": "notification_1784900000"}
```

**Response:**
```json
{"ok": true, "data": {"notification_id": "notification_1784900000", "read": true}}
```

Mark every unread notification:

```json
{"all": true}
```

**Response:**
```json
{"ok": true, "data": {"marked_read": 4}}
```

Exactly one of `notification_id` or `all=true` is required. Unknown notification
IDs return 404.

### List Referred Users

`POST /user?request_type=referral_list`

No body required. Returns the users who registered using the caller's Beyin ID
as their reference code, newest first. Referred users' IDs are **masked**
(first two and last two characters visible) — full IDs are never exposed.

**Response:**
```json
{
  "ok": true,
  "data": {
    "referrals": [
      {
        "beyin_id_masked": "AB**23",
        "joined_at": 1784900000,
        "plan": "starter"
      }
    ],
    "count": 1
  }
}
```

`joined_at` is a Unix timestamp in seconds. `plan` is the referred user's
current plan identifier (`free` when no paid plan is active).

### Redeem Referral Commission

`POST /user?request_type=referral_redeem`

Converts available (unredeemed) referral commission into **Beyin Credits**,
instantly. You earn a commission on referred users' payments — the default rate
is **20%** and may be adjusted per account — and the credited balance is
spendable inside Beyin Finance the same as any other credit.

Commission is redeemed **as credits only** — there is no cash/USDT withdrawal
and therefore no payout or KYC step for referral earnings. (Instructor course
earnings are a separate system with its own payout flow; see the Education API
reference.)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `redeem_type` | string | Yes | Must be `credits` |
| `amount` | number | Yes | USDT-denominated amount, **minimum 1**, at most the available balance |

**Response:**
```json
{"ok": true, "data": {"redeem_type": "credits", "amount": 5.0, "status": "completed"}}
```

Sending any `redeem_type` other than `credits`, or an `amount` below 1, returns
HTTP 400.

### Set Inviter / Referral ID

`POST /user?request_type=set_inviter`

Sets the 6-character Beyin ID of the user who invited the caller. This endpoint is only available if no referral ID has been set previously and the user registered within the last 30 days.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inviter_id` | string | Yes | 6-character uppercase alphanumeric Beyin ID of the inviter |

**Validation Rules:**
- Must be a valid 6-character alphanumeric code (`^[A-Z0-9]{6}$`).
- Cannot be the caller's own Beyin ID.
- Cannot be changed once set.
- Must be submitted within 30 days of the user's registration timestamp (`registered_at`).
- The inviter Beyin ID must exist in the system.

**Response:**
```json
{
  "ok": true,
  "data": {
    "inviter_id": "ABC123",
    "message": "Inviter ID set successfully"
  },
  "timestamp": 1787098000
}
```

---

## User Preferences & Favorites

### Update Favorite Coins

`POST /user?request_type=favorite_coin`

Adds or removes a cryptocurrency trading pair from the user's synced favorites list stored in their profile.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Asset pair symbol, e.g. `BTCUSDT` |
| `action` | string | No | `add` (default) or `remove` |

**Validation Rules:**
- `symbol` is required and automatically converted to uppercase.
- Maximum 100 favorite coins allowed per user profile.

**Response:**
```json
{
  "ok": true,
  "data": {
    "symbol": "BTCUSDT",
    "action": "add",
    "favorites": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
  },
  "timestamp": 1787098000
}
```

---

## Developer API Key Management

Manage your Developer API key. Each user may have **1 active** Developer API
key at a time — to replace it, revoke the existing key and generate a new one.
Generating and revoking a key require JWT authentication. Status can be read by
the authenticated owner; a Developer API key may only retrieve its own status.

### Generate API Key

`POST /user?request_type=api_key_generate`

Creates a new Developer API key. The generated secret is returned **once** and
cannot be retrieved afterward.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Human-readable label for the key (1-64 characters) |
| `permissions` | string[] | No | Stored metadata only; it does not restrict endpoint access. Default: `["read", "trade"]`. Do not use this field as an access-control boundary. |

**Response:**
```json
{
  "ok": true,
  "data": {
    "api_key": "bf_key_a1b2c3d4e5f6a1b2c3d4e5f6",
    "api_secret": "bf_sec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

:::{warning}
The `api_secret` is shown once only — store it securely. It is not retrievable
afterward.
:::

**Errors:**
- 400: "Label must be 1-64 characters"
- 400: "Maximum 1 API key allowed. Delete your existing key first."
- 403: "api_key_generate requires JWT authentication"
- 503: Temporary service unavailability (`"code": "api_key_store_unavailable"`). No key
  was created and no secret was issued; retry the request.

### Get API Key Status

`POST /user?request_type=api_key_status`

Returns the status of your single active Developer API key. Because each user
may hold only one key, this reports whether a key exists and its metadata rather
than a list. A first-party session or the current key may authenticate this
request. The secret is never returned by this operation.

**Response:**
```json
{
  "ok": true,
  "data": {
    "has_key": true,
    "key": {
      "api_key": "bf_key_a1b2c3d4e5f6a1b2c3d4e5f6",
      "label": "Trading dashboard",
      "permissions": ["read", "trade"],
      "created_at": 1787098000
    },
    "max_keys": 1
  }
}
```

When no key exists, `has_key` is `false` and `key` is `null`.

**Errors:**
- 503: Temporary service unavailability (`"code": "api_key_store_unavailable"`);
  retry with backoff.

### Revoke API Key

`POST /user?request_type=api_key_revoke`

Revokes your Developer API key. The key record is deleted permanently and
immediately frees your key slot so you can generate a replacement.
Revocation cannot be undone — issue a new key with `api_key_generate`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | Yes | The API key ID to revoke |

**Response:**
```json
{"ok": true, "data": {"deleted": true}}
```

**Errors:**
- 400: "api_key_id required"
- 403: "api_key_revoke requires JWT authentication"
- 403: "Key not found or not owned by user"
- 503: Temporary service unavailability (`"code": "api_key_store_unavailable"`). The key
  was not deleted and still authenticates; retry the request.

### Authentication Flow (Developer API Keys)

API consumers authenticate by sending both the `X-API-Key` and `X-API-Secret`
headers on every request. The observable behavior is:

1. Valid key and secret: the request is authenticated and processed.
2. Missing, unknown, or revoked credentials: HTTP 401 with
   `"code": "invalid_credentials"`. Revoked keys stop authenticating
   immediately.
3. Credentials could not be evaluated because the service is temporarily
   unavailable: HTTP 503 with `"code": "api_key_store_unavailable"`. Your
   credentials were never checked, so this is not a reason to rotate them —
   retry with backoff.

A rejected or revoked Developer API key never silently downgrades to guest
access. The same 503 applies on `/tradingdata` when `X-API-Key` /
`X-API-Secret` are supplied: an unavailable key store is reported as an outage.

**Limits:** 1 Developer API key per user. Revoking your key frees the slot
immediately so you can issue a replacement.

---

## Economic News

### Get Economic News

`POST /user?request_type=economic_news`

**Free** for every authenticated user — no credit cost and no plan requirement.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Max items per page (default 20, max 50) |
| `cursor` | string | No | Opaque pagination cursor (`next_cursor` from previous page) |
| `last_evaluated_key` | string | No | Alias for `cursor` |

**Example body:**
```json
{
  "limit": 20,
  "cursor": "ZXlKaF..."
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "news": [
      {
        "id": "a3b2c1d4e5f6",
        "type": "news",
        "title": "Fed signals steady policy outlook amid cooling inflation",
        "summary": "FOMC members emphasized balanced risk assessment...",
        "source": "bloomberg",
        "url": "https://...",
        "classification_status": "classified",
        "sentiment": "MILDLY_BULLISH",
        "sentiment_label": "MILDLY_BULLISH",
        "sentiment_score": 2,
        "impact": "HIGH",
        "confidence": 0.88,
        "expected_volatility": "HIGH",
        "category": "FED",
        "affected_coins": ["BTC", "ETH"],
        "affected_markets": ["CRYPTO", "EQUITY"],
        "country": "US",
        "published_at": "2026-08-30T13:30:00+00:00",
        "classified_at": "2026-08-30T13:34:00+00:00",
        "timestamp": 1788096600
      }
    ],
    "has_more": true,
    "next_cursor": "ZXlKaF...",
    "last_evaluated_key": "ZXlKaF...",
    "cost_credits": 0.0
  },
  "timestamp": 1788097000
}
```

`classification_status` is `classified` when the analysis is available and
`unclassified` while a source article is waiting for a successful retry. For
an unclassified item, sentiment, impact, confidence, and volatility are empty
or zero; clients must show that analysis is pending instead of presenting a
neutral rating. Old records without this field are treated as classified.

If no matching items exist, `news` is an empty array. The API does not invent
sample news. **Errors:** 400 if the cursor is invalid; 503 if the data store is
temporarily unavailable.

### Get Economic Calendar

`POST /user?request_type=economic_calendar`

**Free** for every authenticated user — no credit cost and no plan requirement.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Max items per page (default 20, max 50) |
| `mode` | string | No | `"upcoming"` (default) for upcoming events, or `"history"` for past events archive |
| `history` | boolean | No | Alternative to `mode="history"` |
| `horizon_days` | number | No | Number of upcoming days to include when `mode="upcoming"` (default 7, max 30) |
| `cursor` | string | No | Opaque pagination cursor (`next_cursor` from previous page) |
| `last_evaluated_key` | string | No | Alias for `cursor` |

**Example body:**
```json
{
  "limit": 20,
  "mode": "upcoming",
  "horizon_days": 7
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "calendar": [
      {
        "id": "cal_us_cpi_20260830",
        "type": "calendar",
        "title": "Core PCE Price Index m/m",
        "source": "forexfactory",
        "scheduled_date": "2026-08-30T12:30:00Z",
        "event_time": "2026-08-30T12:30:00+00:00",
        "classification_status": "source",
        "impact": "HIGH",
        "forecast": "0.2%",
        "previous": "0.3%",
        "country": "US",
        "timestamp": 1788093000
      }
    ],
    "has_more": true,
    "next_cursor": "ZXlKaF...",
    "last_evaluated_key": "ZXlKaF...",
    "mode": "upcoming",
    "cost_credits": 0.0
  },
  "timestamp": 1788097000
}
```

Calendar entries are ingested directly from the source calendar. Their impact
is the source-provided impact tier; they do not depend on AI news
classification. `classification_status` is `source`. If no matching events
exist, `calendar` is an empty array; no sample events are generated.

**Errors:** 401 if unauthenticated, 400 if the cursor is invalid, or 503 if the
data store is temporarily unavailable.

---

## Strategy


### Create Strategy

`POST /user?request_type=strategy_generate`

Send an `Idempotency-Key` header (8–128 characters; letters, numbers, `.`,
`_`, `:`, and `-`) and preserve it when retrying the same request. The mobile
and web clients generate this header automatically. Reusing the same key with
the same body returns the existing generation attempt without another charge;
reusing it with different inputs returns `409 idempotency_conflict`.

A strategy is **direction-agnostic** and **timeframe-agnostic**: it captures
only the trading logic. The market (spot/futures), side (long/short), leverage
and timeframe are chosen later, at [backtest](#backtest) time, so one
strategy can be evaluated in different run configurations without
regenerating.

#### Strategy fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Unique only within the authenticated user's account; lowercase alphanumeric, no spaces, min 4 chars, max 20 chars, at least 1 letter (`^[a-z0-9]+$`) |
| `signal_mode` | string | Yes | `"signal_orders"` (entry + managed exit) or `"signal_only"` (entry signal only, no TP/SL) |
| `entry_condition` | string | Yes | Entry condition in natural language (max 5000 chars) |
| `tp_condition` | string | `signal_orders` only | Take-profit / exit condition: a percentage-based rule or dynamic candle-window rule (max 2000 chars) |
| `sl_condition` | string | `signal_orders` only | Stop-loss / exit condition: a percentage-based rule or dynamic candle-window rule (max 2000 chars) |

`signal_only` strategies use only the first three fields; the two exit
condition fields are not used for that mode.

The live API currently supports one order-strategy model: a single entry with
one take-profit condition and one stop-loss condition. Each condition can be a
percentage-based rule or a dynamic rule derived from the candle window supplied
by the runtime. Live strategy evaluation may include the current forming candle
so signals do not arrive one candle late; historical backtests exclude the
evaluation candle to prevent look-ahead.
The generator evaluates dynamic rules again for every signal, then returns the
concrete take-profit and stop-loss prices for that signal. The backtest uses
the generated prices together with the entry condition and the holding-time
limit documented below.

:::{note}
Strategies are always created as private. Use `strategy_visibility` to make
public after a successful full_range backtest.
:::

**Cost:** 1 credit. The attempt record, profile state and debit are committed
atomically before generation is queued. The full credit is refunded exactly
once if generation, validation, benchmarking, or queueing fails, so a failed
attempt costs nothing.

**Example body:**
```json
{"strategy_name": "emacross", "signal_mode": "signal_orders", "entry_condition": "EMA 9 crosses above EMA 21", "tp_condition": "For a long, target the largest (high - close) / close gap across the last 100 completed candles; mirror it for a short", "sl_condition": "For a long, stop below the lowest low of the last 20 completed candles; mirror it for a short"}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "version": 1, "signal_mode": "signal_orders", "status": "generating", "generation_id": "8d74f...", "idempotency_key": "9ed15...", "idempotent_replay": false, "cost_upfront": 1.0, "cost_refunded_on_failure": 1.0}}
```

**Errors:** 400 if `strategy_name` or `signal_mode` is invalid, if
`entry_condition` is missing, or if a `signal_orders` request omits
`tp_condition` or `sl_condition`; 402 if insufficient credits; 409 if the
authenticated user already has a strategy with the same name, or if one
`Idempotency-Key` is reused with different inputs (`idempotency_conflict`); 429 with
`reason: "strategy_generation_in_progress"` (plus `Retry-After`) if you already
have the maximum number of generations running. See the
[Common `reason` codes](#common-reason-codes) table.

Generation also applies a safety policy to the user-provided description,
entry, take-profit, stop-loss and revision text. Text that attempts prompt
injection, code execution, secret/system access, network/filesystem access, or
is not a valid trading condition is rejected. The asynchronous generation
attempt becomes `failed`, the full 1-credit charge is refunded once, and its
generation service records HTTP `422` with the machine-readable shape
`{"code":"strategy_input_rejected","reason_code":"unsafe_or_invalid_condition","retryable":false}`.
No generated source is stored for a rejected attempt. Generated strategy source
also has a zero-import policy; safe legacy imports remain readable only for
backward compatibility and are not accepted in new or revised strategy code.

### Get Strategy Detail

`POST /user?request_type=strategy_detail`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Strategy owned by the authenticated user |

Only safe editable/display fields are returned. Strategy source code, owner
credentials and private metadata are not exposed.

**Response:**
```json
{
  "ok": true,
  "data": {
    "strategy_name": "emacross",
    "status": "active",
    "version": 3,
    "signal_mode": "signal_orders",
    "direction_agnostic": true,
    "entry_condition": "EMA 12 crosses above EMA 26",
    "tp_condition": "Price reaches +5%",
    "sl_condition": "Price drops -3%",
    "visibility": "private",
    "credits_per_signal": 0,
    "public_coins": [],
    "candle_count": 32,
    "created_at": 1784000000,
    "updated_at": 1784900000
  }
}
```

`timeframe` is present only if one was chosen; it is otherwise omitted because a
strategy is timeframe-agnostic.

**Errors:** 400 missing strategy name, 404 not found. Strategies are looked up
scoped to the authenticated owner, so a strategy you do not own is reported as
404 (not 403).

### Edit Strategy

`POST /user?request_type=strategy_edit`

This credit-consuming endpoint uses the same `Idempotency-Key` replay and
conflict rules as [Create Strategy](#create-strategy). Preserve the key across
transport or session-refresh retries.

Two modes, selected by `mode`:

- **`rewrite`** — re-enter the strategy's conditions and regenerate the same
  strategy. An order strategy uses `entry_condition`, `tp_condition` and
  `sl_condition`; a signal-only strategy uses only `entry_condition`.
- **`ai_revise`** — send a free-text `revision_prompt` (min 20 chars) describing
  the change; the generator revises the existing code. Conditions are left
  unchanged unless you also send them.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Existing strategy you own |
| `mode` | string | No | `"rewrite"` (re-enter conditions) or `"ai_revise"` (free-text change request). |
| `entry_condition` | string | No | New entry condition |
| `tp_condition` | string | Cond. | New take-profit / exit condition (percentage-based or dynamic). Required with `sl_condition` for a `signal_orders` rewrite. |
| `sl_condition` | string | Cond. | New stop-loss / exit condition (percentage-based or dynamic). Required with `tp_condition` for a `signal_orders` rewrite. |
| `revision_prompt` | string | Cond. | Free-text change request, 20–2000 chars. Required for `mode: "ai_revise"`; rejected for `mode: "rewrite"`. |

The required condition fields mirror [Create Strategy](#create-strategy): the
strategy's `signal_mode` decides whether `tp_condition` and `sl_condition` must
be present.

:::{warning}
Editing a strategy creates a new version and triggers AI code regeneration. All marketplace subscribers of this strategy will be automatically unsubscribed.
:::

**Example body (rewrite an order strategy with exit rules):**
```json
{"strategy_name": "emacross", "mode": "rewrite", "entry_condition": "EMA 12 crosses above EMA 26", "tp_condition": "Price reaches +5%", "sl_condition": "Stop below the lowest low of the last 20 completed candles"}
```

**Example body (AI revise):**
```json
{"strategy_name": "emacross", "mode": "ai_revise", "revision_prompt": "Tighten the stop-loss and add a volume filter to the entry."}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "version": 3, "status": "generating", "generation_id": "302bc...", "idempotency_key": "a198e...", "idempotent_replay": false, "copiers_cancelled": true}}
```

Each accepted rewrite creates the next strategy version; previous versions are
retained. Use [`strategy_versions`](#get-strategy-versions) to list them and
[`strategy_rollback`](#rollback-strategy) to restore one when needed.

### Set Strategy Visibility

`POST /user?request_type=strategy_visibility`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | |
| `visibility` | string | Yes | `"private"` or `"public"` |
| `credits_per_signal` | number | Yes* | 0.1-10 (*required for public) — per-signal fee in credits, charged to a subscriber each time they receive a signal from this strategy |
| `timeframe` | string | Yes* | (*required for public) e.g. `"4h"` |
| `coins` | string[] | Yes* | (*required for public) coins to list |

:::{warning}
Requirements for public: Must have a successful `full_range` backtest. Only coins with **total_return > 0%** are eligible.
:::

**Example body (make public):**
```json
{"strategy_name": "emacross", "visibility": "public", "credits_per_signal": 0.5, "timeframe": "4h", "coins": ["BTC", "ETH", "SOL"]}
```

**Response (public):**
```json
{"ok": true, "data": {"strategy_name": "emacross", "visibility": "public", "credits_per_signal": 0.5, "timeframe": "4h", "eligible_coins": ["BTC", "ETH"], "rejected_coins": {"SOL": "negative_return"}}}
```

**Example body (make private):**
```json
{"strategy_name": "emacross", "visibility": "private"}
```

**Response (private):**
```json
{"ok": true, "data": {"strategy_name": "emacross", "visibility": "private"}}
```

**Errors:** 400 no full_range backtest, 400 no coins with positive return, 400 missing required fields for public.

**How fees work:** When a subscriber receives a signal from your public strategy, `credits_per_signal` is deducted from their balance and credited to you (minus platform fee).

### Get Strategy Versions

`POST /user?request_type=strategy_versions`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |

Each returned version includes `status`: `available` means its strategy code is stored, `generating` means the current version is still being created, and `not_found` means its strategy code is missing. Metadata is optional for older versions. The endpoint returns the full version history.

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "current_version": 3, "versions": [{"version": 1, "created_at": 1784000000, "status": "available"}, {"version": 2, "created_at": 1784500000, "status": "available"}, {"version": 3, "created_at": 1784900000, "status": "generating"}]}}
```

### Rollback Strategy

`POST /user?request_type=strategy_rollback`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `target_version` | number | Yes |

:::{danger}
Rollback sets visibility to private, resets credits_per_signal to 0, and cancels all marketplace subscriptions.
:::

**Example body:**
```json
{"strategy_name": "emacross", "target_version": 2}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "new_version": 4, "rolled_back_to": 2, "visibility": "private", "credits_per_signal": 0, "marketplace_subscriptions_cancelled": 3}}
```

### Delete Strategy

`POST /user?request_type=strategy_delete`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Strategy owned by the authenticated user |
| `confirmation` | string | Yes | Must exactly equal `strategy_name` |

:::{danger}
This is destructive. The client must require the user to type the exact strategy
name. A strategy with an active marketplace listing cannot be deleted; unpublish
it first.
:::

The operation verifies ownership and marketplace state before deletion. If the
request cannot be completed safely, no user-visible strategy data is removed.

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "deleted": true, "deleted_objects": 8}}
```

**Errors:**

- 400: missing name or confirmation mismatch
- 404: strategy not found (a strategy you do not own is also reported as 404,
  because the lookup is scoped to the authenticated owner)
- 409: active marketplace listing must be unpublished first
- 503: the deletion could not be completed safely; nothing was deleted

---

## Backtest

**Endpoint:** `POST /backtest?action=<action>`

The first-party mobile client sends `auth_type: jwt` with a `jwt_token` header
and performs a local readiness/refresh check before estimate, launch, status,
and result calls. Public developer clients remain backward compatible: callers
that omit `auth_type` may use the legacy `beyin_id` + `beyin_password` flow or
the documented API-key flow. A first-party request that declares JWT auth but
omits the token receives `401 {"code": "jwt_required"}` rather than entering
the legacy empty-credential branch.

**Two backtest modes available:**
- **Specified Range** (`action=run`): Test a strategy on a specific date range for a single instrument.
- **Full Range** (`action=full_range`): Test a strategy on all available data for multiple instruments. Required for marketplace publishing.

Use `symbol` for one instrument (for example `BTCUSDT` or `EURUSD`) and
`symbols` for a multi-instrument request (for example `["BTCUSDT",
"ETHUSDT"]`). The instrument catalog resolves each symbol to its available
market data automatically. The resolved asset class, data source, market, and
venue are returned as informational `instrument` metadata; clients do not need
to choose or send a provider or exchange. If a symbol is ambiguous in the
catalog, `asset_class` and `market` can be supplied to identify the intended
dataset. Send either `symbol` or `symbols` in a request, never both.
Legacy `coin` and `coins` request fields remain accepted for existing clients,
but new integrations should use only `symbol` or `symbols`. Some older response
shapes still contain `coin`/`coins` for client compatibility; these are output
labels, not alternate request parameters.

**Execution model (spot/futures, leverage, side) is chosen here, at backtest
time.** Strategies are direction-agnostic (see [Create Strategy](#create-strategy)),
so the `market_type`, `leverage` and `position_side` fields on the launch
actions (`run`, `full_range`, `portfolio`) decide how the same strategy is
executed — spot or futures, long or short. Omitting them falls back to a legacy
strategy's stored values (spot + long by default). `market` here remains the
**dataset** namespace (which candles to read), which is a separate concept from
`market_type` (spot vs futures execution).

**Credit charge:** Each distinct symbol with usable data costs **0.5 Beyin
credits**. A single-symbol `run` costs 0.5 credits; `full_range` and `portfolio`
cost 0.5 credits per symbol that passes data/range validation. The full amount is
reserved before processing starts and is refunded if the job fails. The charge does
not increase with candle count or the number of data windows. `estimate` reports the
same amount that launch will reserve.

**Candle and execution model for new jobs:** All requested timeframes are
rebuilt from chronological 1-minute OHLCV data: open is the first source open,
high/low are the source extremes, close is the latest source close, and volume
is summed. On each available 1-minute update, the engine updates the forming
requested-timeframe candle and evaluates the strategy; it does not wait for
that larger candle to close. A position's
`signal_time` identifies the candle/update that produced the signal, while
`time` records the simulated entry time. Exit checks begin with the next
available 1-minute candle so price movement before the entry is not used.
Missing 1-minute intervals are not synthesized; an incomplete target-timeframe
bucket with a gap is not used as a valid candle.

For multi-symbol jobs, at most two symbols per user are processed at once.
Remaining symbols wait in the job queue; poll `action=status` to show active and
queued symbols and per-symbol progress.

### Estimate Cost

`POST /backtest?action=estimate`

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `strategy_name` | string | Yes | Strategy to test |
| `symbol` | string | One of `symbol` or `symbols` | One instrument, e.g. `BTCUSDT` |
| `symbols` | string[] | One of `symbol` or `symbols` | Multiple instruments from one data market; use for portfolio/full-range estimates |
| `timeframe` | string | Yes | Strategy evaluation timeframe |
| `asset_class` | string | Auto | Optional catalog disambiguation |
| `market` | string | Auto | Optional dataset disambiguation |
| `max_hold_days` | integer | `30` | Affects estimated data lookahead |

**Response:**
```json
{"action": "estimate", "timeframe": "4h", "total_candles": 8334, "source_timeframe": "1m", "source_candles": 2000000, "estimated_cost_credits": 0.5, "credits_per_coin": 0.5, "billable_coins": 1, "estimated_duration_seconds": 31, "estimated_duration_human": "31s", "chunks": 14, "max_active_coins_per_user": 2, "current_credits": 7.35, "can_afford": true}
```

`total_candles` describes the requested timeframe; `source_candles` describes
the 1-minute source data. Duration is an estimate and can change with current
queue load, strategy complexity, warmup data, and the requested maximum holding
period.

### Get Instrument Backtest Info

`POST /backtest?action=info`

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `strategy_name` | string | Yes | Strategy to inspect |
| `symbol` | string | Yes | Instrument, e.g. `BTCUSDT` or `EURUSD` |
| `timeframe` | string | Yes | Requested timeframe |
| `asset_class` | string | Auto | Optional catalog disambiguation |
| `market` | string | Auto | Optional dataset disambiguation |

**Response:**
```json
{"action": "info", "coin": "BTC", "symbol": "BTCUSDT", "instrument": {"asset_class": "crypto", "provider": "binance", "market": "spot", "exchange": "BINANCE", "symbol": "BTCUSDT"}, "timeframe": "4h", "data_range": {"first_ts": 1514764800, "last_ts": 1784476800, "first_date": "2018-01-01", "last_date": "2026-07-19", "total_candles": 18730, "source_timeframe": "1m", "source_candles": 4495200}, "strategy": {"slug": "emacross", "candle_count": 32}, "cost_preview": {"credits_if_full": 0.5, "credits_per_coin": 0.5}, "current_credits": 7.35}
```

### List Available Timeframes

`POST /backtest?action=list_timeframes`

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `symbol` | string | Yes | Instrument, e.g. `BTCUSDT` or `EURUSD` |
| `asset_class` | string | Auto | Optional catalog disambiguation |
| `market` | string | Auto | Optional dataset disambiguation |

**Response:**
```json
{"action": "list_timeframes", "coin": "EURUSD", "symbol": "EURUSD", "instrument": {"asset_class": "forex", "provider": "dukascopy", "market": "forex", "exchange": "FX", "symbol": "EURUSD"}, "timeframes": [{"timeframe": "1d", "suffix": "1DAY", "s3_key": "<opaque data key>"}]}
```

Use the documented timeframe and suffix values. Treat any opaque key in this
response as implementation-defined; clients should not parse it or fetch it
directly.

### Run Specified Range Backtest

`POST /backtest?action=run`

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `strategy_name` | string | Required | Strategy to test |
| `symbol` | string | Required | Tradable symbol from the configured instrument catalog, e.g. `BTCUSDT`, `EURUSD`, or `GOLD` |
| `asset_class` | string | Auto | Catalog-resolved; optional when a symbol is unique |
| `market` | string | Auto | Dataset resolved from the instrument catalog; optional disambiguation |
| `timeframe` | string | Required | Strategy evaluation timeframe, e.g. `4h` |
| `start_ts` / `end_ts` | number | Required | Start and end Unix timestamps |
| `market_type` | string | `spot` | `spot` or `futures` execution model; spot is long-only and 1x |
| `leverage` | number | `3` for futures | Futures leverage, 1–125; spot forces 1x |
| `position_side` | string | `long` | `long` or `short`; spot forces `long`; alias `side` |
| `commission` | number | `0.2` | Round-trip commission percentage |
| `position_pct` | number | `100` | Percent of the current simulated balance committed to each single-run trade; it directly changes the equity curve and final balance |
| `min_gap_candles` | integer | `4` | Minimum strategy-timeframe candle steps between accepted entries; signals inside the gap are skipped |
| `max_hold_days` | integer | `30` | Maximum holding period, 1–365 days; `max_wait_days` remains a legacy alias |
| `min_profit_pct` | number | `0.1` | Minimum TP return after the modeled commission and the default zero-spread assumption are deducted |
| `max_profit_pct` | number | `100` | Maximum entry-to-TP price distance before leverage; leveraged account return may be higher, subject to liquidation; maximum accepted value is 500 |
| `min_loss_pct` | number | `0.1` | Minimum percentage distance from entry price to the stop price |
| `max_loss_pct` | number | `50` | Maximum percentage distance from entry price to the stop price |
| `signal_filter_mode` | string | `clamp` | `clamp` skips TP below the net minimum, caps TP/SL distances above maximums, and moves SL distances below the minimum to the minimum. `reject` skips a signal whenever any configured min/max boundary is violated without changing its prices. |

**Notes:**
- New jobs evaluate strategy conditions on the forming requested-timeframe
  candle as 1-minute source candles arrive. The requested-timeframe candle does
  not need to close before a signal can be produced. `signal_time` is the
  signal's display timestamp; `time` is the simulated entry timestamp.
- `max_hold_days` defaults to 30. If neither TP, SL, nor liquidation closes a
  position before its deadline, it closes at the open of the first available 1-minute candle
  whose timestamp is at or after that deadline. The old `max_wait_days` key remains accepted for
  queued legacy requests.
- **Spread assumption:** this request does not accept a spread estimate. The simulator uses `0%` because a symbol alone does not provide historical spread data. This is separate from `commission` and does not model live slippage.
- **signal_filter_mode = `clamp`** (default): a TP whose net return after modeled costs is below `min_profit_pct` is skipped; TP distances above `max_profit_pct` and SL distances outside the configured min/max range are adjusted to the nearest allowed boundary.
- **signal_filter_mode = `reject`:** a signal is skipped when its TP net return or SL entry distance falls outside the configured min/max range. The engine does not alter TP/SL prices in this mode.
- **min/max profit/loss** values are passed to the strategy function as ratio parameters (`min_profit_ratio`, `max_profit_ratio`, `max_loss_ratio`, `min_loss_ratio`) for TP/SL price calculation.

### Exit scenarios in the completed result

New jobs return one ordinary result plus `summary.exit_scenarios`. The user
chooses which TP reference to display after the backtest; the TP/SL collision
rule is fixed and is not a request option. The default and marketplace view is
`body`. The same entry stream is evaluated against three TP references
using 1-minute candles:

- `body`: long TP is reached when `max(open, close) >= TP`; short TP is reached
  when `min(open, close) <= TP`.
- `midpoint`: long TP is reached when `(max(open, close) + high) / 2 >= TP`;
  short TP is reached when `(min(open, close) + low) / 2 <= TP`.
- `wick`: long TP is reached when `high >= TP`; short TP is reached when
  `low <= TP`.

SL and liquidation checks use the 1-minute wick. If TP and SL are reached in
the same 1-minute candle, SL wins; liquidation takes precedence if its level is
also reached. A long SL fill is the most adverse of the stop, candle open, and
low (`min(open, low, SL)`); a short SL fill is the most adverse of the stop,
candle open, and high (`max(open, high, SL)`). TP fills at its target price.
`all_positions` carries `tp_modes` and aligned arrays named
`scenario_exit_times`, `scenario_exit_prices`, `scenario_results`, and
`scenario_close_types`. The integer `scenario_conflict_mask` uses the same
mode order, with bit 0 for `body`, bit 1 for `midpoint`, and bit 2 for `wick`.
The selected `trades` view includes `same_candle_conflict` when any of those
scenarios had a same-candle TP/SL collision.

`summary.exit_scenarios.scenarios` contains one compact summary and equity
curve for each TP reference. `all_positions` stores shared entry fields once
and aligned arrays for each mode's exit time, price, result, and close type;
the API does not repeat a full trade object for every TP reference. The
selected line can be shown fully opaque while the other two TP references
remain dashed and translucent. Marketplace publication requires `body` TP
with wick-based SL; `midpoint` and `wick` are analysis views.

Previously saved results may retain the exit fields from the engine version
that originally created them. These M1 rules apply to newly launched jobs.

Each strategy signal may calculate its own TP/SL price from the strategy's
conditions. If neither level closes the position before `max_hold_days`, the
backtest applies the maximum holding-time exit (30 days by default).

**Response:**
```json
{"action": "run", "mode": "async_chunked", "job_id": "1784936800_6a2326", "cost_credits": 0.5, "remaining_credits": 6.85, "chunks": 1, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=1784936800_6a2326", "result": "?action=result&job_id=1784936800_6a2326"}}
```

### Full Range Backtest (for Marketplace)

`POST /backtest?action=full_range`

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `strategy_name` | string | Required | Strategy to test |
| `symbol` or `symbols` | string / string[] | Required | One instrument with `symbol`, or multiple instruments with `symbols`; all must resolve to the same data market |
| `timeframe` | string | Required | Strategy evaluation timeframe |
| `asset_class` | string | Auto | Optional catalog disambiguation |
| `market` | string | Auto | Optional dataset disambiguation |
| `max_hold_days` | integer | `30` | Maximum holding period, 1–365 days |

Each requested instrument is processed separately; longer histories may
be split into multiple data windows. New jobs rebuild the selected timeframe
from 1-minute source data. At most two symbols are processed per user at once;
additional symbols wait in the queue and appear in the status response. This
action is required for `marketplace_publish` with `signal_mode=full`.
All symbols in one multi-symbol request must resolve to the same data market.

**Example body:**
```json
{"strategy_name": "emacross", "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"], "timeframe": "4h"}
```

**Response:**
```json
{"action": "full_range", "job_id": "1784936800_fr_abc", "coins": ["BTC", "ETH", "SOL"], "chunks": 3, "cost_credits": 1.5, "remaining_credits": 5.85, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=1784936800_fr_abc", "result": "?action=result&job_id=1784936800_fr_abc"}}
```

### Launch Portfolio Backtest

`POST /backtest?action=portfolio`

Simulates all selected symbols against **one shared balance**. The balance is
split into `divide` position slots: each position uses
`current balance / divide`, at most `divide` positions are open at once, and
at most one position per symbol at a time. Signals that arrive with no free
slot are skipped (and counted). Commission is applied as in single-symbol
runs; spread defaults to 0% because historical spread data is unavailable.

The portfolio uses the same 1-minute source and exit rules as `run`. Set
`max_hold_days` to override the 30-day maximum holding period. At most two symbols
are processed at a time per user; any other selected symbols are queued.

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `strategy_name` | string | Required | Strategy to test |
| `symbols` | string[] | Required | 2–50 instruments from the same data market, e.g. `BTCUSDT` and `ETHUSDT` |
| `asset_class` | string | Auto | Optional catalog disambiguation |
| `market` | string | Auto | Optional shared dataset disambiguation |
| `timeframe` | string | Required | Strategy evaluation timeframe |
| `max_hold_days` | integer | `30` | Maximum holding period, 1–365 days |
| `divide` | integer | Number of symbols | 1–20 position slots |
| `initial_balance` | number | `100` | Shared starting balance |
| `commission` | number | `0.2` | Round-trip commission percentage |
| `start_ts` / `end_ts` | integer | Optional | Unix seconds; omitted means each symbol's full available history |

**Example body:**
```json
{"strategy_name": "emacross", "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"], "timeframe": "4h", "divide": 3, "initial_balance": 100}
```

**Response:**
```json
{"action": "portfolio", "job_id": "pf_1784936800_ab12cd", "coins": ["BTC", "ETH", "SOL"], "divide": 3, "initial_balance": 100, "chunks": 3, "cost_credits": 1.5, "remaining_credits": 5.85, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=pf_1784936800_ab12cd", "result": "?action=result&job_id=pf_1784936800_ab12cd"}}
```

The portfolio result (fetched with `action=result`) contains, in addition to
the standard summary fields: `initial_balance`, `final_balance`, `buy_count`,
`sell_count`, `avg_stop_loss_pct`, `avg_target_pct`, `skipped_no_slot`,
`skipped_coin_busy`, `max_concurrent_positions`; plus top-level
`coin_results` (per-coin summaries), `per_coin_contribution` (dollar PnL by
coin), `trades` (coin-tagged, first 500, `trades_truncated` flag) and
`recommended_divide`:

```json
"recommended_divide": {
  "divide": 5, "final_balance": 214.2, "total_return_pct": 114.2,
  "max_drawdown_pct": 18.3, "max_concurrent_signals": 9,
  "candidates": [{"divide": 1, "total_return_pct": 80.1, "max_drawdown_pct": 31.0, "final_balance": 180.1, "total_trades": 42, "skipped_no_slot": 12}],
  "method": "return_dd_score"
}
```

The recommendation simulates a fixed candidate set of divide values over the
same signal timeline and picks the one maximizing
`final_balance × (1 − max_drawdown/200)` — return lightly penalized by
drawdown.

### Backtest Launch Limits

Backtest launch actions (`action=run`, `full_range`, or `portfolio`) can return
HTTP 429 when the account's current launch limit has been reached. The response
includes `current_running`, `max_concurrent`, and `retry_after`; these counts
describe that account's current request state and are not a platform-wide
throughput guarantee. Follow `Retry-After` before submitting another launch.

When you exceed it, the launch is rejected with HTTP 429 and
`reason: "backtest_concurrency_limit"`:

```json
{
  "error": "You already have the maximum number of backtests running. Wait for one to finish, then try again.",
  "reason": "backtest_concurrency_limit",
  "current_running": 2,
  "max_concurrent": 3,
  "retry_after": 15
}
```

A `Retry-After` header accompanies the response. Jobs already accepted remain
available through the documented status and result actions. Accepted launches
keep returning `"status": "dispatched"` as before. See the
[Common `reason` codes](#common-reason-codes) table for the full contract and
the related `backtest_capacity_exceeded` and `strategy_generation_in_progress`
reasons.

### Get Per-Coin Portfolio Result

`POST /backtest?action=coin_result`

Returns the standalone backtest result of a single coin inside a completed
portfolio job (same shape as a single-coin result: `summary`, `trades`).

| Field | Type | Required |
|-------|------|----------|
| `job_id` | string | Yes |
| `coin` | string | Yes |

### Poll Status

`POST /backtest?action=status`

| Field | Type | Required |
|-------|------|----------|
| `job_id` | string | Yes |

**Response (running):**
```json
{"job_id": "...", "status": "running", "progress_pct": 65, "elapsed_seconds": 42, "estimated_remaining_seconds": 22, "coin_progress": {"BTC": {"status": "running", "progress_pct": 65}, "ETH": {"status": "queued", "progress_pct": 0}}, "active_coins": ["BTC"], "queued_coins": ["ETH"], "max_active_coins_per_user": 2}
```

**Response (failed):**
```json
{"job_id": "...", "status": "failed", "progress_pct": 65, "elapsed_seconds": 42, "estimated_remaining_seconds": 0, "error": "Backtest execution failed"}
```

Failed-job credit recovery is automatic and is not a customer endpoint. The
status response contains only the customer-visible job state.

Status values: `queued`, `running`, `scanning`, `completed`, `failed`. The
per-coin status map and active/queued coin lists let clients explain progress
when a multi-coin job is waiting for earlier coins to finish.

### Get Result

`POST /backtest?action=result`

| Field | Type | Required |
|-------|------|----------|
| `job_id` | string | Yes |

**Response:**
```json
{
  "action": "run", "job_id": "...", "coin": "BTC", "timeframe": "4h",
  "summary": {
    "total_signals": 15, "gain_count": 5, "loss_count": 2, "total_trades": 7,
    "win_rate": 71.43, "final_balance": 105.46, "total_return_pct": 5.46,
    "max_drawdown_pct": 10.45, "profit_factor": 1.38, "avg_profit_per_trade_pct": 0.76,
    "avg_signals_per_month": 0.79, "avg_win_return_pct": 4.97, "avg_loss_return_pct": -9.02,
    "best_trade_pct": 5.33, "worst_trade_pct": -10.45
  },
  "all_positions": [], "trades": [],
  "total_positions": 15, "total_trades": 7, "cost_credits": 0.5
}
```

The result's `summary.exit_scenarios` reports `tp_modes`, the `body` default,
the `wick` stop model, `source_timeframe: "1m"`, and the fixed
`same_candle_policy: "stop_first"`. Each of `scenarios.body`,
`scenarios.midpoint`, and `scenarios.wick` contains its own summary metrics and
equity curve (`final_balance`, `total_return_pct`, `max_drawdown_pct`,
`profit_factor`, `win_rate`, trade counts, and `equity_curve`). Position and
trade records keep shared fields once; `all_positions` has the per-mode arrays
and `trades` contains the default selected trade series. `signal_time` identifies
the signal candle and `time` identifies the simulated entry time.

Result merging is serialized per job. If a merge is still running or the
required result data is still being prepared, `action=result` may return HTTP
202 with a retryable message; poll `action=status` and request the result again.
Incomplete cached payloads are not considered completed results.

New results may include optional market-data quality metadata:
`data_quality` for a single-coin run, or `data_quality_by_coin` for full-range
and portfolio jobs. Each record reports `available_start_ts`,
`available_end_ts`, `incomplete_partitions`, `estimated_missing_candles`, and
`latest_candle_age_seconds`. Missing-candle counts are estimates derived from
the stored one-minute partitions. A full-range backtest includes only data
available in the source store; it does not synthesize history before the
reported start timestamp.

### Get All Trades or Signals

`POST /backtest?action=result_trades`

Reads a paginated trade or signal stream from an already completed job. It does
not start another scan or charge credits.

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `job_id` | string | Required | Completed backtest job ID |
| `coin` | string | Optional | Coin filter for portfolio trade results; ignored when `stream` is `signals` |
| `offset` | integer | `0` | Zero-based row offset |
| `limit` | integer | `100` | Page size, clamped to 1–200 |
| `stream` | string | `trades` | `trades` returns entered orders; `signals` returns entered and skipped signals |

**Example body:**
```json
{"job_id": "1784936800_6a2326", "offset": 0, "limit": 100, "stream": "trades"}
```

**Response:**
```json
{"action": "result_trades", "job_id": "1784936800_6a2326", "offset": 0, "limit": 100, "total": 2450, "has_more": true, "trades": []}
```

### Recalculate Portfolio Divide

`POST /backtest?action=resimulate_divide`

Replays saved positions with a different portfolio allocation. It does not
rerun workers or charge credits.

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `job_id` | string | Required | Completed portfolio backtest job ID |
| `divide` | integer | `1` | Concurrent portfolio slots, clamped to 1–20 |
| `position_mode` | string | `compound` | `compound`, `fixed`, or `risk_pct` |
| `fixed_amount` | number | `0` | Stake per trade when `position_mode` is `fixed` |
| `risk_pct` | number | `0` | Balance percentage used when `position_mode` is `risk_pct` |
| `initial_balance` | number | Saved job value | Optional positive starting-balance override |

**Example body:**
```json
{"job_id": "1784936800_6a2326", "divide": 3, "position_mode": "compound", "initial_balance": 1000}
```

### Walk-Forward Analysis

`POST /backtest?action=walk_forward`

Splits the saved position history into chronological windows and replays those
positions for a robustness comparison. It does not rerun the strategy scan or
charge credits.

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `job_id` | string | Required | Completed backtest job ID |
| `wf_windows` | integer | `4` | Number of chronological windows, clamped to 2–20 |

**Example body:**
```json
{"job_id": "1784936800_6a2326", "wf_windows": 4}
```

### Monte Carlo Analysis

`POST /backtest?action=monte_carlo`

Runs a deterministic block-bootstrap robustness analysis over saved positions.
It does not rerun the strategy scan or charge credits.

| Field | Type | Required / default | Description |
|-------|------|-------------------|-------------|
| `job_id` | string | Required | Completed backtest job ID |
| `mc_runs` | integer | `1000` | Simulation count, clamped to 100–5000 |

**Example body:**
```json
{"job_id": "1784936800_6a2326", "mc_runs": 1000}
```

### Delete Backtest

`POST /backtest?action=delete_backtest`

| Field | Type | Required |
|-------|------|----------|
| `job_id` | string | Conditional | Preferred for async jobs; deletes the job prefix and removes it from the user index |
| `strategy_name` | string | Conditional | Required with `backtest_key` for the legacy stored-result form |
| `backtest_key` | string | Conditional | Required with `strategy_name` when `job_id` is not supplied |

**Response:**
```json
{"action": "delete_backtest", "success": true, "job_id": "1784936800_6a2326", "deleted_objects": 6}
```

The legacy `{strategy_name, backtest_key}` request remains backward compatible.

### Backtest History

`POST /user?request_type=backtest_history`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | No | Filter by strategy |
| `coin` | string | No | Filter by coin (e.g. `"BTC"`) |
| `timeframe` | string | No | Filter by timeframe (e.g. `"4h"`) |
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor from the previous filtered page |

**Example body:**
```json
{"strategy_name": "emacross", "coin": "BTC", "timeframe": "4h"}
```

**Response:**
```json
{"ok": true, "data": {"backtests": [{"job_id": "...", "strategy_name": "emacross", "coin": "BTC", "timeframe": "4h", "cost_credits": 0.5, "created_at": 1784936800, "summary": {"total_trades": 7, "win_rate": 71.43, "total_return_pct": 5.46}}], "count": 1, "last_evaluated_key": "base64...", "has_more": true}}
```

Filtering is applied before pagination. The cursor represents the last
`(created_at, job_id)` pair and must be returned unchanged. Legacy job IDs
recover their timestamp when `created_at` is absent. Malformed cursors and
non-integer page sizes return HTTP 400.

---

## Signals

### Active Signals

`POST /user?request_type=active_signals`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string or string[] | No | Filter by strategy. Single string or array. Omit for all signals. |
| `page_size` | integer | No | Default 25, min 1, max 50 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Example body (single strategy):**
```json
{"strategy_name": "emacross"}
```

**Example body (multiple strategies):**
```json
{"strategy_name": ["emacross", "rsibounce"]}
```

**Example body (all signals):**
```json
{}
```

**Response:**
```json
{"ok": true, "data": {"signals": [{"position_key": "emacross#BTC#1784850000", "coin": "BTC", "strategy_name": "emacross", "owner": "MTHG7A", "side": "LONG", "signal_mode": "signal_orders", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "source": "user", "created_at": 1784850000}], "count": 1, "last_evaluated_key": "base64...", "has_more": true}}
```

Return the opaque cursor unchanged. Malformed cursors and non-integer page
sizes return HTTP 400.

### Signal History

`POST /user?request_type=signal_history`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filters` | object | No | Filter object (see below) |
| `page_size` | number | No | Default 20, max 50 |
| `last_evaluated_key` | string | No | Pagination cursor (base64) |

**Filter object fields:**

| Field | Type | Description |
|-------|------|-------------|
| `coin` | string | Filter by coin |
| `strategy_name` | string | Filter by strategy |
| `owner` | string | Filter by signal owner |

**Example body:**
```json
{"filters": {"coin": "BTC", "strategy_name": "emacross"}, "page_size": 20}
```

**Response:**
```json
{"ok": true, "data": {"signals": [{"closed_key": "...", "coin": "BTC", "strategy_name": "emacross", "side": "LONG", "signal_mode": "signal_orders", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "exit_price": "69500.00", "result": "GAIN", "source": "user", "created_at": 1784850000, "closed_at": 1784950000}], "count": 1, "last_evaluated_key": "base64...", "has_more": true}}
```

Return the opaque cursor unchanged. Malformed cursors and non-integer page
sizes return HTTP 400. Filters are evaluated on each result page; clients
must continue while `has_more` is true even if a filtered page is empty.

---

## Marketplace

### Browse Listings

`GET /tradingdata?request_type=marketplace_browse&limit=50`

Guest-accessible: this endpoint may be called without authentication and is
subject to service-level protections. When credentials are supplied the caller
identity is tracked for audit and entitlement checks.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `market_type` | string | No | `"spot"` or `"futures"` |
| `timeframe` | string | No | e.g. `"4h"` |
| `coin` | string | No | Filter by one listed coin |
| `limit` | number | No | Default 50, min 1, max 100 |
| `cursor` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "owner": "MT***A", "description": "EMA crossover strategy", "market_type": "spot", "asset_class": "crypto", "provider": "binance", "exchange": "binance", "data_source": "binance", "trading_enabled": true, "timeframe": "4h", "signal_mode": "full", "leverage": 1, "listed_coins": ["BTC", "ETH"], "billing_period": "monthly", "monthly_price_credits": 2, "signal_price_credits": 2, "status": "active", "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "subscriber_count": 5, "total_signals_delivered": 42, "created_at": 1784000000, "is_owner": false, "subscription_status": "", "selected_coins": []}], "count": 1, "next_cursor": "base64...", "has_more": true}
```

Send the returned cursor unchanged to fetch the next page. `has_more=false`
and a null cursor identify the final page. Malformed cursors and non-integer
page sizes return HTTP 400 instead of silently restarting at page one.

### Listing Detail

`GET /tradingdata?request_type=marketplace_listing&listing_id=lst_abc123`

Guest-accessible and subject to service-level protections. The public response
masks owner data and does not include caller-specific ownership
or subscription state. Use the authenticated `/user` listing-detail endpoint
below when those fields are needed.

For the authenticated caller's ownership and subscription state, use:

`POST /user?request_type=marketplace_listing_detail`

This authenticated form adds `is_owner`, `subscription_status`, and
`selected_coins` for the caller.

The public `GET /tradingdata` response is the unwrapped listing object. The
`ok`/`data` envelope shown below is the authenticated `/user` response.

| Field | Type | Required |
|-------|------|----------|
| `listing_id` | string | Yes |

**Response:**
```json
{
  "ok": true,
  "data": {
    "listing_id": "lst_abc123",
    "strategy_name": "emacross",
    "owner": "MT***A",
    "description": "EMA crossover strategy",
    "market_type": "spot",
    "asset_class": "crypto",
    "provider": "binance",
    "exchange": "binance",
    "data_source": "binance",
    "trading_enabled": true,
    "timeframe": "4h",
    "leverage": 1,
    "signal_mode": "full",
    "listed_coins": ["BTC", "ETH"],
    "billing_period": "monthly",
    "monthly_price_credits": 2,
    "signal_price_credits": 2,
    "total_pnl_pct": 12.5,
    "win_rate_pct": 68.0,
    "subscriber_count": 5,
    "total_signals_delivered": 42,
    "created_at": 1784000000,
    "is_owner": false,
    "subscription_status": "active",
    "selected_coins": ["BTC"]
  }
}
```

`is_owner` is evaluated for the authenticated caller. When that caller has a
deterministic subscription for the listing, `subscription_status` and
`selected_coins` describe it; otherwise they are an empty string and list.

**Errors:** 404 listing not found (or removed and not owner).

### Subscribe

`POST /user?request_type=marketplace_subscribe`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing_id` | string | Yes | |
| `selected_coins` | string[] | Yes | Must be subset of listed_coins |

**Validations:** Valid license required. Cannot self-subscribe. Plan coin/strategy limits apply.

**Example body:**
```json
{"listing_id": "lst_abc123", "selected_coins": ["BTC", "ETH"]}
```

**Response:**
```json
{"ok": true, "data": {"subscription_id": "sub_5c9f...", "listing_id": "lst_abc123", "strategy_name": "emacross", "active_coins": ["BTC", "ETH"], "billing_period": "monthly", "monthly_price_credits": 2, "signal_price_credits": 2, "credits_charged": 2, "next_charge_at": 1786600000, "expires_at": 1786600000, "bindings_created": 2}}
```

The subscription ID is deterministic for the authenticated user and listing.
The subscription is all-or-nothing; a failed request leaves no partial
subscription.

**Errors:** 400 invalid coins / coin limit / self-subscribe / listing not active, 402 insufficient credits (`"code": "insufficient_credits"` — your balance is below the listing's `monthly_price_credits`), 403 license expired or active-strategy plan limit, 404 listing not found, **410 listing no longer accepts new subscribers**, 409 duplicate subscription or binding conflict, 503 atomic commit unavailable.

### Unsubscribe

`POST /user?request_type=marketplace_unsubscribe`

| Field | Type | Required |
|-------|------|----------|
| `subscription_id` | string | Yes |

**Response:**
```json
{"ok": true, "data": {"status": "active", "auto_renew": false, "subscription_id": "sub_xyz789", "expires_at": 1786600000, "bindings_removed": 0}}
```

Unsubscribe turns off renewal but does not end the prepaid period immediately.
The subscription remains active, and its bindings remain usable until
`expires_at`; the scheduled billing process ends it when that period finishes.

### My Listings

`POST /user?request_type=marketplace_my_listings`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"ok": true, "data": {"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "status": "active", "signal_mode": "full", "market_type": "spot", "asset_class": "crypto", "provider": "binance", "exchange": "binance", "data_source": "binance", "trading_enabled": true, "timeframe": "4h", "listed_coins": ["BTC"], "billing_period": "monthly", "monthly_price_credits": 2, "signal_price_credits": 2, "subscriber_count": 5, "total_signals_delivered": 42, "total_credits_earned": 100.0, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "created_at": 1784000000}], "last_evaluated_key": "base64...", "has_more": true}}
```

### My Subscriptions

`POST /user?request_type=marketplace_my_subscriptions`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"ok": true, "data": {"subscriptions": [{"subscription_id": "sub_xyz789", "listing_id": "lst_abc123", "creator_beyin_id": "ABC123", "selected_coins": ["BTC"], "status": "active", "end_reason": "", "auto_renew": true, "billing_period": "monthly", "monthly_price_credits": 2, "signal_price_credits": 2, "signals_received": 12, "credits_spent": 2.0, "next_charge_at": 1786600000, "expires_at": 1786600000, "ended_at": 0, "created_at": 1784000000, "divide": 1, "scope": "", "run_config": {}}], "last_evaluated_key": "base64...", "has_more": true}}
```

For both account lists, return the cursor unchanged to fetch the next result
page. Malformed cursors and non-integer page sizes return HTTP 400.

### Publish Strategy

`POST /user?request_type=marketplace_publish`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_key` | string | Yes | Lowercase letters and numbers only |
| `description` | string | No | Max 500 chars, no HTML |
| `monthly_price_credits` | number | Yes | 0.1 - 10 — fixed MONTHLY subscription fee in credits (billing is always monthly, prepaid) |
| `signal_mode` | string | No | `"full"` (default) or `"signal_only"` |
| `requested_coins` | string[] | Yes | Non-empty list of coins to list |

:::{warning}
Requirements for `signal_mode=full`: Must have a successful `full_range` backtest using the auditable `body` TP + `wick` SL model. Only coins with positive return, at least 10 trades, and a per-trade geometric gain strictly above 1.001 are listed; others are rejected (`negative_return`, `insufficient_trades`, `low_per_trade_gain`, or `no_backtest_data`). A new result with an incompatible exit model is rejected as `exit_model_not_marketplace_compatible`. `signal_mode=signal_only` requires no backtest and lists every requested coin.
:::

Marketplace listing names are globally disambiguated by appending the creator's
Beyin ID to the user's local strategy name. For example, a local strategy named
`test1` owned by `ABC123` is listed as `test1_ABC123`. Other users may still
create their own local `test1` strategy.

**Example body:**
```json
{"strategy_key": "emacross", "description": "EMA crossover for BTC", "monthly_price_credits": 2, "signal_mode": "full", "requested_coins": ["BTC", "ETH", "SOL"]}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "strategy_key": "emacross_ABC123", "strategy_name": "emacross_ABC123", "display_strategy_name": "emacross", "status": "active", "listed_coins": ["BTC", "ETH"], "rejected_coins": {"SOL": "negative_return", "DOGE": "insufficient_trades"}, "monthly_price_credits": 2, "billing_period": "monthly", "signal_mode": "full", "backtest_summary": {"BTC": {"pnl_pct": 12.5, "win_rate": 68.0, "trades": 42}}}}
```

**Errors:** 400 invalid `strategy_key`, 400 invalid `signal_mode`, 400 `monthly_price_credits` out of range (0.1-10), 400 empty `requested_coins`, 400 HTML in description, 400 no `full_range` backtest found (full mode), 400 no eligible coins (`"code": "no_eligible_coins"`), 404 strategy not found.

### Update Listing

`POST /user?request_type=marketplace_update_listing`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing_id` | string | Yes | |
| `monthly_price_credits` | number | No | 0.1 - 10 — new monthly subscription fee |
| `description` | string | No | Max 500 chars, no HTML |

:::{danger}
Changing the price stops renewal for existing subscribers; their prepaid period
and bindings remain active until expiry.
:::

**Example body:**
```json
{"listing_id": "lst_abc123", "monthly_price_credits": 3, "description": "Updated description"}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "updated_fields": ["monthly_price_credits"], "subscriptions_renewal_stopped": 3, "note": "Price changed 2 -> 3. Existing subscribers keep their prepaid period; auto-renew is turned off."}}
```

Changing the price stops auto-renewal for existing subscribers but does not
remove their bindings or end their already-paid period. New subscribers use the
new price.

**Errors:** 400 nothing to update / invalid price / HTML in description, 400 listing not active, 403 not your listing, 404 listing not found.

### Unpublish Listing

`POST /user?request_type=marketplace_unpublish`

| Field | Type | Required |
|-------|------|----------|
| `listing_id` | string | Yes |

:::{warning}
Stops renewal for existing subscriptions, hides the listing from new buyers, and
keeps the listing active until the last prepaid rider period ends.
:::

**Response:**
```json
{"ok": true, "data": {"status": "active", "accepting_subscribers": false, "riders_notified": 5}}
```

Unpublishing hides the listing from browse and blocks new subscriptions. Existing
subscribers keep access until their prepaid `expires_at`; renewal is disabled and
the listing is finalized after the last rider's prepaid period ends.

### Submit Review

`POST /user?request_type=marketplace_review`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing_id` | string | Yes | |
| `rating` | number | Yes | 1-5 |
| `comment` | string | No | Max 500 chars |

:::{note}
Must have (or had) a subscription to review. One review per user per listing. Cannot review own listing. If a comment is supplied it must be **at least 10 characters** and may **not contain URLs** (`http://`, `https://`, or `www.`); disallowed markup is rejected.
:::

**Errors:** 400 rating out of range / comment too short / URL in comment / disallowed content, 403 not a subscriber, 404 listing not found, 400 cannot review own listing.

**Example body:**
```json
{"listing_id": "lst_abc123", "rating": 4, "comment": "Great strategy, consistent returns!"}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "rating": 4, "avg_rating": 4.2, "review_count": 8}}
```

### Get Reviews

`GET /tradingdata?request_type=marketplace_reviews&listing_id=lst_abc123&limit=20`

Guest-accessible: callable without authentication, subject to service-level
protections. When credentials are supplied the caller identity is tracked for
rate limiting, audit and entitlement checks.

| Query parameter | Type | Required |
|-------|------|----------|
| `listing_id` | string | Yes |
| `limit` | number | No | Default 20, max 50 |
| `cursor` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"listing_id": "lst_abc123", "reviews": [{"review_id": "7c6c...", "rating": 5, "comment": "Great strategy!", "timestamp": 1784900000}], "count": 1, "next_cursor": "base64...", "has_more": true}
```

`review_id` is a deterministic, privacy-safe hash; the source account identifier used
for duplicate prevention is never returned. Send the cursor unchanged for the
next page. Malformed cursors and non-integer limits return HTTP 400.

---

## Trading Data

Most Trading Data requests accept an authenticated caller, but a subset is
**guest-accessible** (callable without credentials, subject to service-level
protections) — see the guest list in the [Authentication](#authentication)
section. Endpoints not on that list require a tracked caller identity and
return HTTP 401 without one. Some responses may still be license-gated by plan
after the caller is identified (for example, `trend_signals` pages beyond the
first).

### Trend Signals

`GET /tradingdata?request_type=trend_signals&page=0&limit=50`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | number | No | Page number (default 0). Page > 0 requires license. |
| `limit` | number | No | Items per page (default 50, max 50; values above 50 are clamped) |

**Response:**
```json
{"items": [{"coin_name": "BTC", "graph_type": "4h", "timestamp": "1784900000", "way": "BUY", "is_return_to_trend": false}], "page": 0, "count": 10, "last_page": false}
```

Collection items are lightweight discovery records. Request a selected signal
through `trend_signal_detail` for its metadata and trend-line anchors; fetch
historical candles separately when rendering a full chart.

### Trend Signal Detail

`GET /tradingdata?request_type=trend_signal_detail&coin_name=BTC&graph_type=240&timestamp=1784900000`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `coin_name` | string | Yes | e.g. `"BTC"` |
| `graph_type` | string | Yes | Signal timeframe exactly as returned by the list. It may be a formatted value such as `"4h"` or a minute value such as `"15"`. |
| `timestamp` | string | Yes | Signal timestamp |

**Response:**
```json
{"item": {"coin_name": "BTC", "graph_type": "4h", "timestamp": "1784900000", "way": "BUY", "is_return_to_trend": false, "trend_data": {"low_trend": [["1784800000000", 12, "67200.5"], ["1784900000000", 90, "68120.0"]]}, "klines_data": []}}
```

`trend_data` contains the calculated high/low trend-line anchor points. Each
point is `[timestamp_ms, candle_index, price]`; the two values are anchors,
not candles. The client draws the line from anchor 1 through anchor 2 and
stops it at the break candle. This response does not provide the full candle
history; use the documented candle-history endpoint when the chart needs it.

### Market Ticker

`GET /tradingdata?request_type=market_ticker&market=spot&page=0&limit=500`

Returns the market list used by the official app. Clients must call this Beyin
Finance API endpoint; they must not call exchange ticker endpoints directly.
The API filters ticker rows through server-maintained exchange metadata so only
symbols currently enabled for trading in the selected market are returned.

Price and quantity precision metadata may exist server-side for symbols that
are not currently trading, but those symbols are excluded from this ticker
catalog until they become trading-enabled again.

Use the precision and symbol metadata returned by the documented market
endpoints. Values can vary by instrument; treat the latest API response as
authoritative and do not depend on a separate file or storage layout.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `market` | string | No | `spot` or `futures` (default `spot`) |
| `page` | number | No | Page number (default 0) |
| `limit` | number | No | Items per page (default 500, max 1000) |
| `query` | string | No | Alphanumeric symbol search, e.g. `BTC` |
| `favorites` | string | No | Comma-separated USDT symbols prioritized first |

**Response:**
```json
{
  "items": [
    {
      "symbol": "BTCUSDT",
      "last_price": "67200.10",
      "change_percent_24h": "1.25",
      "quote_volume_24h": "123456789.0",
      "market_type": "spot",
      "price_precision": 2,
      "favorite": false
    }
  ],
  "page": 0,
  "count": 1,
  "total": 420,
  "last_page": false
}
```

If live exchange ticker data is temporarily unavailable, the API may return a
recent verified cache and include `_cache.stale=true`. Clients should show a
stale-data warning when `_cache` is present.

### Market Quote

`GET /tradingdata?request_type=market_quote&symbol=BTCUSDT&market=spot`

Returns a lightweight live quote for chart order preparation. This endpoint
does not submit orders and does not require user Binance credentials. It is
guest-accessible (callable without authentication, subject to service-level
protections); when credentials are supplied the caller is tracked.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Binance USDT pair, e.g. `BTCUSDT` |
| `market` | string | No | `spot` or `futures` (default `spot`) |

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "market_type": "spot",
  "bid_price": "67200.10",
  "ask_price": "67200.20",
  "last_price": "67200.15",
  "spread": "0.10",
  "spread_percent": "0.0001488",
  "commission_rate": "0.001",
  "commission_percent": "0.1",
  "taker_commission_rate": "0.001",
  "maker_commission_rate": "0.001",
  "taker_commission_percent": "0.1",
  "maker_commission_percent": "0.1",
  "bids": [["67200.10", "0.50"]],
  "asks": [["67200.20", "0.40"]],
  "depth_limit": 100,
  "depth_source": "binance_depth",
  "timestamp": 1784900000000
}
```

For `market=futures`, the response also includes:

```json
{
  "mark_price": "67200.12",
  "funding_rate": "0.0001",
  "next_funding_time": "1784908800000"
}
```

Clients should refresh this endpoint at a low frequency suitable for UI
previews, currently 5 seconds in the mobile chart. Any real order preview or
submission must revalidate bid/ask, funding, commission, precision, notional,
and risk limits server-side.

### Binance Klines

`GET /tradingdata?request_type=get_klines&symbol=BTCUSDT&interval=1h&limit=100&market=spot`

Returns historical Binance candles for Spot or USDⓈ-M Futures market data.
The route is guest-accessible; callers do not send personal Binance
credentials.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | USDT pair, e.g. `BTCUSDT` |
| `interval` | string | No | Default `1h`. Supported: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M` |
| `limit` | integer | No | Default 100, min 1, max 1000 |
| `market` | string | No | `spot` (default) or `futures` |
| `start_time` | integer | No | Inclusive Unix epoch in milliseconds |
| `end_time` | integer | No | Inclusive Unix epoch in milliseconds |

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "market": "spot",
  "klines": [{
    "open_time": 1784900000000,
    "open": "67000.00",
    "high": "67200.00",
    "low": "66900.00",
    "close": "67100.00",
    "volume": "12.5",
    "close_time": 1784903599999,
    "fetched_at": 1784903600000
  }],
  "count": 1,
  "fetched_at": 1784903600000
}
```

The response is cached briefly. HTTP 400 means Binance rejected the symbol or
interval; HTTP 502 indicates an upstream or fetch failure.

### Market Symbol Info

`GET /tradingdata?request_type=market_symbol_info&symbol=BTCUSDT`

Guest-accessible lookup for current instrument availability and exchange
precision/filter metadata. The result is informational; live order preview
remains authoritative because exchange filters can change.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | USDT pair such as `BTCUSDT`; `coin` is accepted as an alias |

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "spot": true,
  "futures": true,
  "spot_price_precision": 2,
  "futures_price_precision": 2,
  "spot_qty_precision": 5,
  "futures_qty_precision": 3,
  "spot_tick_size": "0.01",
  "spot_quantity_step_size": "0.00001",
  "spot_market_quantity_step_size": "0.00001",
  "spot_oco_quantity_step_size": "0.00001",
  "spot_min_quantity": "0.00001",
  "spot_market_min_quantity": "0.00001",
  "spot_min_notional": "5",
  "spot_min_notional_apply_to_market": true,
  "futures_max_leverage": 5
}
```

Filter values can be `null` when the current manifest does not contain them.
Do not use missing filter data to submit a live order; `binance_order_preview`
returns an error until the filters are available.

### Market Live (Forex and Commodities)

`GET /tradingdata?request_type=market_live&category=forex&query=EUR`

Returns the cached live quote list for Dukascopy forex or commodity
instruments. This route is guest-accessible and does not use Binance keys.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | string | Yes | `forex` or `commodities` |
| `query` | string | No | Case-insensitive substring match against symbol or display name |
| `favorites` | string | No | Comma-separated exact symbols; filters the list before `query` |

**Response:**
```json
{
  "items": [{
    "symbol": "EURUSD",
    "display_name": "EUR/USD",
    "asset_class": "forex",
    "provider": "dukascopy",
    "data_source": "Data provided by Dukascopy",
    "trading_enabled": false,
    "market_type": "forex",
    "last_price": "1.08",
    "change_percent_24h": "0",
    "quote_volume_24h": "0",
    "price_precision": 5,
    "open_time": 1784899940000,
    "updated_at": 1784900000000
  }],
  "page": 0,
  "last_page": true,
  "source": "dukascopy",
  "stale": false
}
```

Each quote item also carries `asset_class`, `provider`, `data_source`,
`trading_enabled`, `market_type`, `change_percent_24h`, `quote_volume_24h`,
`price_precision`, `open_time`, and `updated_at`. The current cache writes
`change_percent_24h` and `quote_volume_24h` as `"0"`; they are placeholders,
not calculated performance or volume figures. `stale` is currently returned
as `false` by the route and does not independently verify quote age.

An empty list means no cached result is currently available for that category.

### Market Candles (Forex and Commodities)

`GET /tradingdata?request_type=market_candles&category=commodities&symbol=GOLD&timeframe=1h&limit=200`

Returns historical candles for supported Dukascopy instruments. The handler
uses a short in-memory cache, then fetches Dukascopy data, and then attempts a
stored-data fallback.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | string | Yes | `forex` or `commodities` |
| `symbol` | string | Yes | Dukascopy symbol such as `EURUSD` or `GOLD` |
| `timeframe` | string | No | Default `1h`; `interval` is an alias. Supported: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `1d` |
| `limit` | integer | No | Default 200; clamped to 200–500 |

**Response:**
```json
{
  "klines": [{"open_time": 1784900000000, "open": "1.08", "high": "1.09", "low": "1.07", "close": "1.085", "volume": "0", "close_time": 1784903600000}],
  "candles": [{"open_time": 1784900000000, "open": "1.08", "high": "1.09", "low": "1.07", "close": "1.085", "volume": "0", "close_time": 1784903600000}],
  "symbol": "EURUSD",
  "interval": "1h",
  "timeframe": "1h",
  "source": "dukascopy",
  "count": 1
}
```

The `candles` and `klines` arrays currently contain the same rows. If neither
historical source is available, a live-price fallback may return a single
synthetic candle; do not treat that fallback as a historical series.

### Sentiment Breakout Signals

`GET /tradingdata?request_type=sentiment_breakout_signals&limit=500`

Guest-accessible persisted breakout entries for `BTCUSDT#1h#breakout`. Results
are returned oldest-first so they can be aligned with candle history.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | integer | No | Default 500, min 1, max 500 |
| `before_timestamp` | integer | No | Return signals with a timestamp earlier than this Unix timestamp in seconds |

**Response:**
```json
{
  "market_key": "BTCUSDT#1h#breakout",
  "signals": [{"timestamp": 1784900000, "direction": "LONG", "entry_price": "67000.00", "score": 72}],
  "count": 1,
  "limit": 500,
  "has_more": true,
  "oldest_timestamp": 1784900000,
  "next_before_timestamp": 1784900000
}
```

Send `next_before_timestamp` unchanged as `before_timestamp` for the next
page. When `has_more` is false, `next_before_timestamp` is `null`.

### Market Sentiment

`GET /tradingdata?request_type=trend_indicator&market_key=BTCUSDT%231h`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `market_key` | string | No | Format: `SYMBOL#timeframe` (default: `BTCUSDT#1h`) |

**Response:**
```json
{"market_key":"BTCUSDT#1h","item":{"market_key":"BTCUSDT#1h","timestamp":1784900000,"score":72,"direction":"BULLISH"},"count":1,"live_candle":{"symbol":"BTCUSDT","market":"spot","interval":"1h","open_time":1784900000000,"open":"118000.00","high":"118250.00","low":"117950.00","close":"118180.00","volume":"12.34","close_time":1784903599999,"is_closed":false,"fetched_at":1784901200000,"age_seconds":0,"cache_status":"fresh"},"live_candle_status":"fresh"}
```

The product fields are `score` (integer sentiment score) and `direction`
(e.g. `"BULLISH"` / `"BEARISH"` / `"NEUTRAL"`). The `item` object may carry
additional fields; **treat any field not documented here as unstable and
ignore it** — do not depend on its presence, name, or value.

For the default `BTCUSDT#1h` key, `live_candle` is a separate, in-progress BTC
spot candle. Its OHLC values describe the current hour so far, and `close` is
the latest sampled price. `open_time`, `close_time`, and `fetched_at` are Unix
timestamps in milliseconds. `is_closed` becomes `true` after that candle has
ended. `age_seconds` reports how old the shared sample is; clients should treat
`cache_status` / `live_candle_status` values `fresh`, `stale`, and
`unavailable` accordingly. The sample is shared and refreshed no more than once
per 60-second window; a client may poll this endpoint to observe updates. When
unavailable, `live_candle` is `null`. The persisted `item` and the history
endpoint remain closed-candle sentiment records and are not rewritten by this
live price data.

### Sentiment History

`GET /tradingdata?request_type=trend_indicator_history&market_key=BTCUSDT%231h&limit=50`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `market_key` | string | No | Default: `BTCUSDT#1h` |
| `limit` | number | No | Max 200 (default 200) |
| `before_timestamp` | number | No | Pagination: get items before this timestamp |

**Response:**
```json
{"market_key": "BTCUSDT#1h", "items": [{"timestamp": 1784900000, "score": 72, "direction": "BULLISH"}], "count": 50, "limit": 50, "has_more": true, "oldest_timestamp": 1784720000, "next_before_timestamp": 1784720000}
```

---

## General Config & Platform Data

### Get Platform Config

`GET /`

Public — no authentication required. This is the startup configuration the
client fetches before login. Returns platform metadata such as banners and
supported assets. Cache locally and ignore unknown fields.

**Response:**
```json
{
  "GENERAL": "general",
  "banner_urls": ["https://..."],
  "supported_coins": ["BTC", "ETH", "SOL"],
  "active_payments": ["shopier", "binance"],
  "payment_gateways": {
    "shopier": {"enabled": true, "base_url": "https://www.shopier.com/beyinfinance"},
    "binance": {"enabled": true, "binance_account_id": "86382681"}
  },
  "maintenance_mode": false,
  "config": {"maintenance_mode": false},
  "latest_app_version": "0.0.17",
  "min_supported_app_version": "0.0.1",
  "changelog_url": "https://beyinfinance.com/changelog/"
}
```

The example is representative; the response may include additional platform
configuration fields. The public payment configuration exposes the Binance
Account ID used for manual transfers.

### Get Available Coins

`POST /user?request_type=available_coins`

No body params. Returns coins that are TRADING on Binance AND have kline data available for backtest/signals.

**Response:**
```json
{"ok": true, "data": {"coins": ["ADA", "AVAX", "BNB", "BTC", "DOGE", "DOT", "ETH", "LINK", "SOL", "XRP"], "count": 285}}
```

Cache this response; the available set changes infrequently.

### Get Platform Notifications

`GET /tradingdata?request_type=platform_notifications&limit=20`

Guest-accessible and subject to service-level protections. Returns system
announcements such as new features and maintenance messages.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 20, max 50 |

**Response:**
```json
{"notifications": [{"title": "New Feature", "body": "Marketplace is now live!", "type": "announcement", "timestamp": 1784900000}], "count": 1}
```

### Get Changelog

`GET /tradingdata?request_type=changelog&limit=50`

Guest-accessible and subject to service-level protections. Returns the platform
release history: the current and minimum-supported app versions
plus dated release entries. Use it to render a "What's New" screen or to decide
whether to prompt for an app update.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Max entries returned. Default 50, max 200 |
| `since_version` | string | No | Only return entries at or above this app version (for example `0.0.6`) |

**Response:**
```json
{"current_version": "0.0.6", "latest_build": 6, "min_supported_version": "0.0.1", "released": [{"version": "0.0.1", "date": "2026-08-12"}], "entries": [{"title": "Community image and comment fixes", "date": "2026-09-10", "items": ["The image is no longer cropped and opens full screen with pinch zoom."]}]}
```

An entry with a `null` `date` is an uncategorized note attached to the most
recent release. When no changelog has been published yet, `entries` is an empty
list and the version fields are `null`.

---

## AI and Market Data

All AI requests use the short `/ai` resource. Integrator requests use the same
`X-API-Key` + `X-API-Secret` credentials described above. The old `/user` and
`/tradingdata` AI routes are retired and return `410 ai_endpoint_moved`.

### AI Chat

`POST /ai?request_type=ai_chat`

```json
{"message": "BTC için 1 saatlik görünüm nedir?"}
```

The `message` value is required and limited to 4,000 characters. A successful
request deducts `0.03` credits and returns `cevap` plus optional structured
`veri`. If the AI service is temporarily unavailable, that charge is refunded
and the endpoint returns HTTP 503. Insufficient credits return HTTP 402 with
`{"hata":"Yetersiz kredi","gerekli":0.03}`.

**Response:**
```json
{"cevap": "...", "veri": {"coin": "BTCUSDT", "market_ratings": []}}
```

Chat history is available with `POST /ai?request_type=ai_chat_history&limit=50`.
The history response is `{"messages":[{"role":"user|assistant","content":"...","timestamp":1784900000}]}`;
`limit` defaults to 50 and is capped at 100.

### Market Analysis

`POST /ai?request_type=market_analysis`

Returns direct market data without generating a chat response. Send `coin` and
optional `vade` in the body.

### Market Commentary

`POST /ai?request_type=market_commentary`

Send `coin` and the previously returned `veri` object to receive a concise
Turkish dashboard commentary. The response is `{"yorum":"..."}`.

### Market Ratings

`POST /ai?request_type=market_ratings`

Send `coin` (optional; defaults to `BTCUSDT`) and receive the multi-timeframe
`market_ratings` list. The response is `{"coin":"BTCUSDT","market_ratings":[]}`.
This is a technical rating feed, not a trade execution endpoint.

---

## Community

### Global Chat - Send Message

`POST /user?request_type=community_chat_message`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Max 500 characters |
| `channel` | string | No | `global` (default), `lang:tr`, `lang:en`, or an authorized leader channel |
| `reply_to_id` | string | No | Message ID to quote/reply to |

**Response:**
```json
{"ok": true, "data": {"msg_id": "1784990000_MTHG7A", "sort_key": "1784990000#1784990000_MTHG7A", "channel": "global"}}
```

### Global Chat - History

`GET /tradingdata?request_type=community_chat&limit=50`

Guest-accessible for reading visible community messages, subject to service-level
protections. Use the returned `next_cursor` as the `cursor`
query parameter for the next page.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 1000, max 1000 |
| `cursor` | string | No | Cursor returned by the previous page |
| `channel` | string | No | `global` (default), `lang:tr`, or `lang:en`; leader channels are not available on this public route |

**Response:**
```json
{"messages": [{"beyin_id": "MTHG7A", "message": "BTC looking bullish!", "created_at": "1784990000", "sort_key": "..."}], "count": 50, "has_more": true, "next_cursor": "1784980000#..."}
```

Pass `next_cursor` back as `cursor` to request the next page.
The cursor is `null` and `has_more=false` on the final page.

### Global Chat - Delete Message

`POST /user?request_type=community_chat_delete`

Soft-deletes a chat message. Two callers are authorized:

- a **channel moderator** (admin, or the leader who owns the channel) may delete
  any message in that channel,
- the **author** may delete their own message.

Any other caller receives `403`. The message row is kept and its text is replaced
with a placeholder (`Bu mesaj silindi` for an author deletion,
`Bu mesaj admin tarafından silindi` for a moderator deletion) so thread replies
stay intact.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sort_key` | string | Yes | `sort_key` of the message to delete |
| `channel` | string | No | Channel identifier, default `global` |

**Response:**
```json
{"ok": true, "data": {"sort_key": "1784990000#1784990000_MTHG7A", "deleted": true, "deleted_by_author": true}, "timestamp": 1784990100}
```

| Status | Code | Meaning |
|--------|------|---------|
| 400 | — | `sort_key` missing, or `channel` is not a valid channel |
| 401 | `session_expired` | No valid session or API key |
| 403 | `forbidden` | Not a moderator and not the author |
| 404 | `not_found` | Message does not exist in that channel |

### Create Post (Leaders Only)

`POST /user?request_type=community_post_create`

Only users with `community_role: "leader"` can create posts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Post title |
| `content` | string | Yes | Max 5000 characters |
| `image_url` | string | No | HTTPS URL for the attached image |
| `category` | string | No | `analysis` (default), `market`, `strategy`, `signal`, `news`, or `education` |
| `image_keys` | string[] | No | Up to 3 keys returned by `community_upload_url` |

**Response:**
```json
{"ok": true, "data": {"post_id": "post_MTHG7A_1784990000"}}
```

Followers are automatically notified through their configured channels.

### List Posts

`GET /tradingdata?request_type=community_posts&limit=20`

Guest-accessible for reading visible leader posts, subject to service-level
protections. Pagination uses the opaque `next_cursor` response
value as the next request's `cursor`.
The feed is returned newest-first by `created_at`. Clients must request bounded
pages instead of loading the entire community feed at once.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | integer | No | Default 20, min 1, max 50 |
| `cursor` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"posts": [{"post_id": "...", "author_id": "MTHG7A", "title": "BTC Analysis", "content": "...", "image_url": "", "like_count": "12", "comment_count": "3", "created_at": "1784990000"}], "count": 20, "has_more": true, "next_cursor": "eyJwb3N0X2lkIjp7IlMiOiIuLi4ifX0="}
```

The cursor is opaque and must be sent back unchanged. Malformed cursors return
HTTP 400 instead of silently restarting at the first page.

### Delete Own Post

`POST /user?request_type=community_post_delete`

Authentication is required. Only the post author can delete the post.
Deletion is immediate for readers: the post is marked hidden and no longer
appears in Akış or Profilim. The record is retained for moderation/audit for 15
days, then permanently removed.

| Field | Type | Required |
|-------|------|----------|
| `post_id` | string | Yes |

**Response:**
```json
{"ok": true, "data": {"post_id": "...", "deleted": true, "delete_after": 1786286000}}
```

**Errors:**
- `400` — `post_id` missing
- `403` — caller is not the post author, or the post is already hidden
- `404` — post not found in the table
- `500` — unexpected database error (logged server-side, not surfaced raw)

### List Author's Posts (Profile)

`POST /user?request_type=community_post_list`

Returns paginated posts for a specific author. Used by the Profilim tab to
display the authenticated user's own posts with per-post delete actions.
Requires authentication.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `author_id` | string | No | Beyin ID of the author; omit to read the global community feed |
| `limit` | integer | No | Default 20, max 50 |
| `last_evaluated_key` | string | No | Opaque cursor returned by previous page |

**Response:**
```json
{"ok": true, "data": {"posts": [{"post_id": "...", "title": "BTC Analysis", "created_at": "1784990000", "like_count": "3", "comment_count": "1"}], "count": 20, "last_evaluated_key": "base64...", "has_more": true}}
```

Posts are sorted newest-first via the `author-index` GSI with
`ScanIndexForward=False`. Send `last_evaluated_key` unchanged as the cursor
for the next page; a malformed cursor returns HTTP 400.

### Like Post

`POST /user?request_type=community_post_like`

| Field | Type | Required |
|-------|------|----------|
| `post_id` | string | Yes |

**Response:**
```json
{"ok": true, "data": {"post_id": "...", "action": "liked"}}
```

**Errors:** 409 if already liked.

### Comment on Post

`POST /user?request_type=community_post_comment`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `post_id` | string | Yes | |
| `comment` | string | Yes | Max 300 characters |

**Response:**
```json
{"ok": true, "data": {"post_id": "...", "comment_id": "comment_MTHG7A_1784990000", "action": "commented"}}
```

### Report Content

`POST /user?request_type=community_post_report`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `post_id` | string | Conditional | For reporting a post |
| `type` | string | No | `"post"` (default) or `"chat"` |
| `sort_key` | string | Conditional | For reporting a chat message |
| `channel` | string | No | Chat channel when `type="chat"` (default `global`) |
| `reason` | string | No | Short report reason (default `other`, max 120 characters) |

**Response:**
```json
{"ok": true, "data": {"action": "reported"}}
```

### Follow Leader

`POST /user?request_type=community_follow`

| Field | Type | Required |
|-------|------|----------|
| `leader_id` | string | Yes |

**Response:**
```json
{"ok": true, "data": {"leader_id": "MTHG7A", "action": "followed"}}
```

### Unfollow Leader

`POST /user?request_type=community_unfollow`

| Field | Type | Required |
|-------|------|----------|
| `leader_id` | string | Yes |

**Response:**
```json
{"ok": true, "data": {"leader_id": "MTHG7A", "action": "unfollowed"}}
```

### List Leaders

`GET /tradingdata?request_type=community_leaders&limit=25`

Guest-accessible and subject to service-level protections.
`is_following` is evaluated for the authenticated caller (and is `false` for
guests); follow and unfollow actions use the `/user` endpoints and require
authentication.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | integer | No | Default 25, min 1, max 50 |
| `cursor` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"leaders": [{"beyin_id": "MTHG7A", "name": "CryptoTrader", "bio": "Full-time crypto analyst", "is_following": false}], "count": 1, "next_cursor": "base64...", "has_more": true}
```

Return the opaque cursor unchanged; malformed cursors return HTTP 400.

### List Accounts I Follow

`GET /tradingdata?request_type=community_following`

Requires an authenticated account. The result is read from the caller's
following records rather than only from the current leader directory, so
accounts remain visible if their leader role changes.

**Response:**
```json
{
  "following": [{
    "beyin_id": "MTHG7A",
    "name": "CryptoTrader",
    "nickname": "cryptotrader",
    "bio": "Market educator",
    "avatar_url": "https://example.com/avatar.jpg",
    "community_verified": true,
    "is_verified": true,
    "is_following": true,
    "post_count": 8,
    "comment_count": 23,
    "total_likes": 41,
    "follower_count": 125
  }],
  "count": 1
}
```

### Apply for Community Leader

`POST /user?request_type=community_leader_apply`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | Leader Display Name (3-30 Latin alphanumeric chars or spaces, e.g. `"Finans Kulubu"`) |
| `reason` | string | Yes | Reason for application (must be non-empty) |
| `experience` | string | Yes | Trading experience details (must be non-empty) |

The system automatically generates a unique lowercase nickname by removing spaces from `display_name` (e.g. `"Finans Kulubu"` -> `"finanskulubu"`). Returns 409 Conflict if nickname is already taken by another user.

`has_500_followers` must be `true` (you confirm you have at least 500 followers).
Optional social links: `twitter`, `instagram`, `youtube`, `telegram`.

If you already have a **pending** application, calling this again **updates**
it in place (edit your submission) rather than failing. An **approved** leader
cannot re-apply (409).

**Response:**
```json
{
  "ok": true,
  "data": {
    "status": "pending",
    "display_name": "Finans Kulubu",
    "nickname": "finanskulubu",
    "applied_at": 1784990000,
    "updated": false,
    "message": "Application submitted. We will review and notify you."
  }
}
```

### Get Leader Application Status

`POST /user?request_type=community_leader_application_get`

Returns the caller's latest leader application so a client can show its status
and prefill the edit form. No body required.

**Response:**
```json
{
  "ok": true,
  "data": {
    "status": "pending",
    "is_leader": false,
    "display_name": "Finans Kulubu",
    "reason": "...",
    "experience": "...",
    "applied_at": 1784990000,
    "twitter": "",
    "instagram": "",
    "youtube": "",
    "telegram": ""
  }
}
```

`status` is one of `none`, `pending`, `approved`, `rejected`, or `withdrawn`.
An approved leader returns `{"status": "approved", "is_leader": true}`; a user
who never applied returns `{"status": "none", "is_leader": false}`.

### Withdraw Leader Application

`POST /user?request_type=community_leader_application_withdraw`

Cancels a **pending** leader application. The record is marked `withdrawn`
(history is kept) and you may apply again later. No body required.

**Response:**
```json
{"ok": true, "data": {"status": "withdrawn"}}
```

**Errors:** 404 if there is no application, 409 if the latest application is not
pending (already approved/rejected/withdrawn).

### Update Leader Profile

`POST /user?request_type=community_leader_update`

Only accessible by users with approved `"leader"` community role.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | New Leader Display Name (3-30 Latin alphanumeric chars or spaces) |
| `bio` | string | No | Updated bio / description |
| `avatar_url` | string | No | Optional new avatar image URL |
| `avatar_key` | string | No | Key returned by `community_upload_url` for a validated uploaded avatar (alias: `avatar_s3_key`) |

**Response:**
```json
{
  "ok": true,
  "data": {
    "display_name": "Finans Kulubu Pro",
    "nickname": "finanskulubupro",
    "community_bio": "Crypto & Forex specialist",
    "avatar_url": "https://...",
    "avatar_s3_key": "<opaque avatar key>"
  }
}
```

---


## Errors

All errors return:
```json
{"error": "Descriptive error message"}
```

Authentication-related errors add an optional machine-readable `code` marker.
The rest of the body shape is unchanged:
```json
{"error": "Invalid JWT token!", "code": "session_expired"}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Credential rejected, revoked, or session token expired |
| 402 | Insufficient credits |
| 403 | Forbidden / license expired |
| 404 | Not found |
| 405 | Invalid request_type |
| 409 | Conflict (duplicate) |
| 429 | Rate limited |
| 500 | Server error |
| 502 | Upstream exchange did not return a usable response |
| 503 | A required service is temporarily unavailable |

### Error `code` markers

`code` is optional. When present it identifies the class of authentication
failure so clients can react without parsing the message text.

| `code` | Meaning | Client action |
|--------|---------|---------------|
| `session_expired` | The session token itself was missing, invalid, or expired. | Clear the stored session and re-authenticate. |
| `invalid_credentials` | The Developer API key/secret was rejected or has been revoked. | Issue new API credentials. |
| `api_key_store_unavailable` | Credentials could not be evaluated because a required service was temporarily unavailable. Always paired with HTTP 503. | Retry with backoff. Do not rotate credentials and do not clear the session. |
| `jwt_required` | A first-party `/backtest` request declared `auth_type=jwt` but did not carry a JWT header. | Wait for session readiness or sign in again; do not fall back to empty legacy credentials. |
| `invalid_token` | The JWT supplied to the backtest surface is malformed, expired, or otherwise invalid. | Refresh the session when possible; otherwise clear it and sign in again. |
| `session_revoked` | The session is no longer accepted. | Clear the local session and sign in again. |

`api_key_store_unavailable` indicates a temporary service failure, not a
rejected credential: it is never a 401 and never a bare 500. It applies to
`api_key_generate`, `api_key_revoke`, `X-API-Key` /
`X-API-Secret` authentication on `/user`, and the same header pair on
`/tradingdata`, `/backtest`, and `/ai`. Invalid or incomplete Developer API
credentials use HTTP 401 with `invalid_credentials`; clients should retry a
503 and must not treat it as a request to replace their credentials.

`session_expired` is returned for a missing, malformed, or expired session
token, for a missing caller identity, and for every operation that rejects an
unauthenticated caller on `/user` and `/tradingdata`. The dedicated
`token_expired` response carries it as well:

```json
{"error": "token_expired", "code": "session_expired", "message": "Your session has expired. Please log in again."}
```

**Clients must clear the local session and re-authenticate only when a 401
carries `"code": "session_expired"`.** A 401 without a `code` field is a
business error, not a session problem, and must not sign the user out.

### Account linking and login status codes

These conditions previously returned HTTP 401. They now return a
condition-specific status, so a client no longer mistakes them for an expired
session:

| Condition | Status |
|------|---------|
| Binance API key or secret is not exactly 64 characters, on the credential-**linking** path (`"Invalid API or Secret key"`) | 400 |
| Binance API key or secret is not exactly 64 characters, on the **login** path (`"Invalid API or Secret key"`) | 401 |
| Binance returned no account ID while linking (`"Could not retrieve Binance ID from API"`) | 502 |
| Login with a Binance identity that is not registered (`"Binance ID not found!"`) | 400 |
| Login where the supplied Google identity does not match the stored one (`"Google ID mismatch!"`) | 409 |

None of these responses carry a `code` marker. In particular, the 401 on the
login path above is a business error, **not** a `session_expired` — clients must
follow the rule above and only sign out on `"code": "session_expired"`.


### Backtest estimate modes

`POST /backtest?action=estimate` accepts the common strategy, coin(s), and
timeframe fields. Without timestamps it estimates a multi-coin `full_range`
operation, including its success charge. When both `start_ts` and `end_ts` are
provided it estimates a single-coin `run`, clips the timestamps to available
data, and returns the range candle count and standard run cost. Supplying only
one timestamp, an inverted range, or multiple coins in range mode returns 400.
The response includes `mode`, either `full_range` or `range`.

---

## Track Trend Break Signal

Track trend break signals to your personal watchlist. Tracked signals are preserved (do not expire via TTL) as long as at least one user is tracking them.

:::{note}
The previously published `track_signal`, `untrack_signal` and `tracked_signals`
names have been removed and now return 405. Use the canonical names below.
:::

### Track a Trend Break Signal

`GET /tradingdata?request_type=track_trend_break_signal`

Adds the authenticated user to a signal's tracking list and removes the signal's TTL (preventing automatic expiration).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `coin_name` | string | Yes | Coin symbol (e.g. `"BTC"`) |
| `graph_type` | string | Yes | Timeframe in minutes (e.g. `"240"`) |
| `way` | string | Yes | Signal direction: `"BUY"` or `"SELL"` |
| `timestamp` | string | Yes | Signal epoch timestamp in seconds |

**Response:**
```json
{"tracked": true}
```

**Errors:**
- 400: Missing required fields
- 401: Authentication required (`"code": "session_expired"`)
- 404: Signal not found (expired or never existed)

### Untrack a Trend Break Signal

`GET /tradingdata?request_type=untrack_trend_break_signal`

Removes the authenticated user from a signal's tracking list. If no users remain tracking the signal, the TTL is re-applied and the signal will eventually expire.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `coin_name` | string | Yes | Coin symbol |
| `graph_type` | string | Yes | Timeframe in minutes |
| `way` | string | Yes | Signal direction |
| `timestamp` | string | Yes | Signal epoch timestamp |

**Response:**
```json
{"tracked": false}
```

**Errors:**
- 400: Missing required fields
- 401: Authentication required (`"code": "session_expired"`)

### Get Tracked Trend Break Signals

`GET /tradingdata?request_type=tracked_trend_break_signals`

Returns all trend break signals the authenticated user is currently tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | integer | No | Max items per page (default 20, max 50) |
| `last_key` | string | No | JSON-encoded pagination cursor from previous response |

**Response:**
```text
{
  "items": [
    {
      "coin_name": "BTC",
      "graph_type": "240",
      "way": "BUY",
      "timestamp": "1720000000",
      "is_return_to_trend": false,
      "klines_data": [...],
      "trend_data": {"high_trend": [...], "low_trend": [...]}
    }
  ],
  "last_key": null
}
```

Tracked items use the documented public signal fields and may include `klines_data` when available. Use `trend_signal_detail` for signal metadata and trend-line anchors, and the candle-history endpoint for chart candles. Clients should rely only on the documented response fields.

**Errors:**
- 401: Authentication required (`"code": "session_expired"`)
