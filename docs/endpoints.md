# Beyin Finance Developer API Reference

**Base URL:** Provided in your API credentials dashboard.

---

## Authentication

Use developer API credentials for integrations. Official app/web clients may
use the authenticated session token issued at login.

| Client | Authentication |
|--------|----------------|
| Developer/integration client | `X-API-Key` + `X-API-Secret` |
| Trading Data routes | `X-API-Key` + `X-API-Secret` or authenticated app session |

**Developer API-key example:**

```
X-API-Key: bf_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
X-API-Secret: bf_sec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

Generate API keys from the Telegram bot, web dashboard, or mobile app.

A missing or invalid credential returns HTTP 401. Every `/tradingdata`, `/user`,
and `/backtest` operation in this reference requires a tracked caller identity
unless the endpoint is explicitly part of login or registration.

A 401 caused by the session token itself carries `"code": "session_expired"` in
the error body; a 401 caused by a rejected or revoked Developer API key carries
`"code": "invalid_credentials"`. Not every 401 is a session problem — see the
Errors section for the marker table and the rule for when a client should
re-authenticate.

If the Developer API key store cannot be reached, the request never reaches a
credential decision: it returns HTTP 503 with
`"code": "api_key_store_unavailable"`. That is an outage to retry, not a
credential to replace.

### Telegram Bot Scope

The Telegram bot is an account handoff and notification channel. It can create
or link a Beyin Finance account, show account and plan information, deliver
signals, manage signal automation preferences, and guide manually confirmed
Binance order actions. It is not a separate market-data source, and clients must
still use the Beyin Finance API endpoints documented here.

### Request correlation

Clients may send a unique `X-Correlation-ID` header for every logical API
request and reuse it across automatic retries. The API accepts only 8-128 characters
from letters, numbers, `.`, `_`, `:`, and `-`; invalid values are replaced.
User API and backtest responses echo the accepted value in
`X-Correlation-ID`. Browser clients may read it through
`Access-Control-Expose-Headers`.

---

## Rate Limits

Rate limits can vary by account and endpoint. Use the response headers as the
authoritative limit for the authenticated client.

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 120        # Your per-minute limit
X-RateLimit-Remaining: 87     # Requests remaining in current window
X-RateLimit-Reset: 1784990340 # Unix timestamp when the window resets
```

When rate limited (HTTP 429):
```
Retry-After: 15               # Seconds until reset
```

### Plan Limits

| Plan | Monthly | Annual (-50%) | Rate Limit (req/min) | Max Active Strategies | Max Coins/Strategy |
|------|---------|---------------|---------------------|----------------------|-------------------|
| Free | – | – | 30 | 0 | 0 |
| Starter | $10 | $60 | 30 | 1 | 5 |
| Plus | $20 | $120 | 60 | 2 | 10 |
| Pro | $50 | $300 | 120 | 5 | 25 |
| Investor | $100 | $600 | 240 | 10 | 50 |

> First-party (app/web) requests receive 2× the listed rate limit.

### Payment

Payments are processed manually via **Binance Pay**.

- **Binance Pay ID:** `863 826 81`
- **Minimum payment:** 1 USDT
- **Exchange rate:** 1 USDT = 1 Beyin Credit
- Subscription duration is proportional to the amount sent.
- Payments over 6 months receive an additional **6 months free**.
- **First payment bonus:** The first minimum 1 USDT payment grants a **1-month demo** of the selected plan.

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
    "BTC": {"status": "completed", "progress_pct": 100},
    "ETH": {"status": "running", "progress_pct": 45}
  }
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

**Common `reason` codes:**
- `rate_limit_exceeded`: User per-minute API request rate limit exceeded.
- `temporarily_unavailable`: The request cannot be processed at this moment.

**Recommended Handling:**
Clients must inspect the `Retry-After` header (or `retry_after` JSON field) and apply exponential backoff with random jitter before retrying the request.

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
        "market_type": "spot",
        "leverage": 1
      }
    }
  }
}
```

Connection values are booleans only. Referral entries use the documented
identifier, amount and status fields.

### Get Login History

`POST /user?request_type=login_history`

Returns the most recent known login for each retained IP origin, newest first.
The authentication record keeps a bounded set of origins; repeated logins from
the same IP update that origin rather than creating duplicate events.

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
      {"transaction_id": "deposit#payment-1", "type": "deposit", "amount": 5.0, "action": "deposit", "description": "Payment abc12345", "timestamp": 1784900000}
    ],
    "count": 3,
    "last_evaluated_key": "base64...",
    "has_more": true
  }
}
```

**Transaction actions:** `deposit`, `backtest`, `credit_adjustment`, `strategy_generate`, `strategy_success`, `economic_news`, `marketplace_signal`

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

Records are ordered newest first. `order_history_id` is the stable
duplicate-removal key. Return the opaque cursor unchanged; malformed cursors,
invalid statuses and non-integer page sizes return HTTP 400. Undocumented fields and
stored exchange/credential payloads are removed from the response.

**Response:**
```json
{
  "ok": true,
  "data": {
    "orders": [
      {
        "order_id": "ord_1784936800",
        "timestamp": 1784936800,
        "strategy_name": "emacross",
        "coin": "BTC",
        "exchange_order_status": "NEW",
        "execution_mode": "real_trade",
        "order_source": "signal",
        "linked_signal_id": "sig_1784850000"
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

Uses the same request fields as `binance_order`, but does **not** place an
exchange order. The API applies exchange precision rules, validates TP/SL
direction, checks minimum notional requirements and verifies the authenticated
account's available balance before returning the irreversible-operation
summary. OCO is currently supported for Spot only. A successful preview is not
a balance reservation; execution repeats validation because market/account
state can change.

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
    "minimum_notional": 10,
    "balance_asset": "BTC",
    "available_balance": "0.010",
    "required_balance": "0.001",
    "balance_verified": true,
    "order_source": "signal",
    "linked_signal_id": "sig_1784850000",
    "irreversible": true
  }
}
```

Use `price_precision` and `quantity_precision` from this response to format all price
and quantity strings in the subsequent `binance_order` request.

The client must obtain a successful preview and require explicit user
confirmation before calling `binance_order`.

### Place Binance OCO Order

`POST /user?request_type=binance_order`

Places an OCO (One-Cancels-Other) order on Binance. Combines a Take-Profit limit order and a Stop-Loss stop-limit order. When one triggers, the other is automatically cancelled.

Requires Binance API keys linked.

:::{important}
Before using this endpoint, the user's Binance API key must have the **Enable Spot & Margin Trading** permission enabled in Binance. The key must also restrict access to trusted IPs and include the Beyin Finance Binance proxy static IP in the Binance API whitelist:

`3.120.214.198`

Orders sent through Beyin Finance are routed to Binance from this static IP, so Binance may reject order placement if the IP is not whitelisted.
:::

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | e.g. `"BTCUSDT"` |
| `side` | string | Yes | `"BUY"` or `"SELL"` - your entry side (OCO exit side is inverted) |
| `quantity` | string | Yes | Amount to sell/buy when TP or SL triggers (formatted to `quantity_precision`) |
| `entry_price` | string | No | Optional reference entry price (formatted to `price_precision`) |
| `take_profit_price` | string | Yes | Take-profit limit price (formatted to `price_precision`) |
| `stop_loss_price` | string | Yes | Stop-loss trigger price (formatted to `price_precision`) |
| `market_type` | string | No | `"spot"` (default). Futures OCO is currently rejected. |
| `order_source` | string | Yes | `"signal"` when entering an active Signal + Orders signal; `"independent"` for an order not linked to a signal |
| `linked_signal_id` | string | Conditional | Opaque signal identifier required for `order_source=signal`; forbidden for independent orders |
| `idempotency_key` | string | Yes | 16-128 letters, numbers, `_` or `-`; generate before preview and reuse for every retry |

:::{warning}
All price and quantity values **must** be formatted as strings using the exchange precision
returned by `binance_order_preview`. Use `price_precision` for all price fields and
`quantity_precision` for quantity. Binance rejects orders with incorrect decimal precision.

Example: If `price_precision: 2` → send `"67000.00"` not `67000` or `"67000.001"`.
If `quantity_precision: 3` → send `"0.001"` not `0.001` or `"0.0010"`.
:::

:::{note}
- Prices and quantities must be sent as strings formatted to the exchange precision returned by preview. The API validates precision and rejects misformatted values.
- During preview and immediately before a real submission, the API validates
  account balance and order constraints again.
- The same idempotency key must be reused for retries of the same logical order.
- For `order_source=signal`, provide the opaque linked signal identifier returned
  by the signal endpoint.
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
  "linked_signal_id": "sig_1784850000",
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
    "orders": [
      {"symbol": "BTCUSDT", "orderId": 111, "type": "LIMIT_MAKER"},
      {"symbol": "BTCUSDT", "orderId": 222, "type": "STOP_LOSS_LIMIT"}
    ],
    "linked_signal_id": "sig_1784850000",
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

The client must not create a new key or blindly resubmit while an order is in a
processing state. Show the order status to the user and poll order history.

**Errors:**
- 400: Missing/non-finite/non-numeric fields, invalid source/link combination, Futures market, precision/minimum-notional failure, insufficient available balance, or invalid idempotency key
- 404: A linked active signal does not exist for the authenticated user
- 409: The key was reused with a different order, or the linked signal does not match the symbol
- 503: Balance or order submission could not be verified; the order was not submitted

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

Converts available (unredeemed) referral commission into Beyin Credits or a
pending USDT withdrawal request.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `redeem_type` | string | Yes | `credits` (instant) or `withdrawal` (pending review) |
| `amount` | number | Yes | USDT amount, minimum 1, at most the available balance |

**Response (credits):**
```json
{"ok": true, "data": {"redeem_type": "credits", "amount": 5.0, "status": "completed"}}
```

**Response (withdrawal):**
```json
{"ok": true, "data": {"redeem_type": "withdrawal", "amount": 5.0, "status": "pending"}}
```

Requesting more than the available commission balance returns HTTP 400 with
`Insufficient commission balance`.

---

## Developer API Key Management

Manage multiple Developer API keys per account. Each user may have up to
**3 active** Developer API keys simultaneously. These endpoints require JWT
authentication (API key auth is not allowed for key management operations).

### Generate API Key

`POST /user?request_type=api_key_generate`

Creates a new Developer API key. The generated secret is returned **once** and
cannot be retrieved afterward.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Human-readable label for the key (1-64 characters) |
| `permissions` | string[] | No | Permission scopes. Default: `["read", "trade"]` |

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
- 400: "Maximum 3 active API keys allowed"
- 403: "api_key_generate requires JWT authentication"
- 503: API key store unavailable (`"code": "api_key_store_unavailable"`). No key
  was created and no secret was issued; retry the request.

### List API Keys

`POST /user?request_type=api_key_list`

Lists all Developer API keys (active and revoked) for the authenticated user.
No body required.

**Response:**
```json
{
  "ok": true,
  "data": {
    "keys": [
      {
        "api_key": "bf_key_a1b2c3d4e5f6a1b2c3d4e5f6",
        "label": "Trading Bot",
        "permissions": ["read", "trade"],
        "created_at": 1720000000,
        "active": true
      }
    ],
    "max_keys": 3
  }
}
```

**Errors:**
- 503: API key store unavailable (`"code": "api_key_store_unavailable"`)

### Revoke API Key

`POST /user?request_type=api_key_revoke`

Revokes a Developer API key (soft-delete, sets `active = false`). Revoked keys
can no longer authenticate API requests.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | Yes | The API key ID to revoke |

**Response:**
```json
{"ok": true, "data": {"revoked": true}}
```

**Errors:**
- 400: "api_key_id required"
- 403: "api_key_revoke requires JWT authentication"
- 403: "Key not found or not owned by user"
- 503: API key store unavailable (`"code": "api_key_store_unavailable"`). The key
  was not revoked; retry the request.

### Authentication Flow (Developer API Keys)

API consumers authenticate using `X-API-Key` and `X-API-Secret` headers:

1. Backend looks up the key in the `BeyinFinanceApiKeys` table.
2. If found and active: verifies `SHA-256(X-API-Secret) == stored hash`.
3. If not found: falls back to legacy `api_key_id-index` GSI on
   BeyinFinanceUsers (backwards compatible).
4. If found but revoked (`active = false`): request is rejected with HTTP 401
   and `"code": "invalid_credentials"`.
5. If the key store itself cannot answer the lookup: HTTP 503 with
   `"code": "api_key_store_unavailable"`. Your credentials were never evaluated,
   so this is not a reason to rotate them — retry with backoff.

A rejected or revoked Developer API key never carries `session_expired`, so an
authenticated app session remains valid. The same 503 applies on
`/tradingdata` when `X-API-Key` / `X-API-Secret` are supplied: an unavailable
key store is reported as an outage, never silently downgraded to a guest
(unauthenticated) session.

:::{note}
Legacy single-key authentication via the `api_key_id-index` GSI on
BeyinFinanceUsers remains functional for backwards compatibility. Existing
integrations using the original single-key system continue to work without
modification.
:::

**Limits:** Maximum 3 active Developer API keys per user.

---

## Economic News

### Get Economic News

`POST /user?request_type=economic_news`

**Cost:** 0.01 credits per request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Max items (default 20, max 50) |

**Example body:**
```json
{"limit": 10}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "news": [
      {"id": "a3b2c1d4e5f6", "type": "news", "title": "Fed issues enforcement action", "source": "fed", "source_url": "https://...", "sentiment": "NEUTRAL", "impact": "MEDIUM", "category": "FED", "affected_coins": ["BTC"], "timestamp": 1784900000}
    ],
    "cost_credits": 0.01
  }
}
```

**Errors:** 402 if insufficient credits.

### Get Economic Calendar

`POST /user?request_type=economic_calendar`

**Cost:** 0.01 credits per request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Max items (default 30, max 50) |

**Example body:**
```json
{"limit": 20}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "calendar": [
      {"id": "f6e5d4c3b2a1", "type": "calendar", "title": "CPI m/m (USD)", "source": "forexfactory", "scheduled_date": "2026-07-28T12:30:00-04:00", "impact": "HIGH", "forecast": "0.2%", "previous": "0.3%", "country": "USD"}
    ],
    "cost_credits": 0.01
  }
}
```

**Errors:** 402 if insufficient credits.

---

## Strategy


### Create Strategy

`POST /user?request_type=strategy_generate`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Unique only within the authenticated user's account; lowercase alphanumeric, no spaces, min 4 chars, max 20 chars, at least 1 letter (`^[a-z0-9]+$`) |
| `market_type` | string | Yes | `"spot"` or `"futures"` |
| `signal_mode` | string | Yes | `"signal_orders"` or `"signal_only"` |
| `timeframe` | string | Yes | `1m,3m,5m,15m,30m,1h,2h,4h,1d` |
| `entry_condition` | string | Yes | Entry condition in natural language |
| `tp_condition` | string | Yes* | Take profit (*required for signal_orders) |
| `sl_condition` | string | Yes* | Stop loss (*required for signal_orders) |
| `position_side` | string | Conditional | `"long"` or `"short"`. Required when `market_type` is `"futures"` AND `signal_mode` is `"signal_orders"`. Ignored otherwise. Determines signal direction for futures strategies. |

:::{note}
Strategies are always created as private. Use `strategy_visibility` to make public after a successful full_range backtest.
:::

**Cost:** 0.20 credits total (0.05 upfront + 0.15 on success)

**Example body:**
```json
{"strategy_name": "emacross", "market_type": "spot", "signal_mode": "signal_orders", "timeframe": "4h", "entry_condition": "EMA 9 crosses above EMA 21", "tp_condition": "Price reaches +3%", "sl_condition": "Price drops -2%"}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "version": 1, "signal_mode": "signal_orders", "status": "generating", "cost_upfront": 0.05, "cost_on_success": 0.15}}
```

**Errors:** 400 if strategy_name is invalid (too short, too long, or contains invalid characters); 400 if `position_side` is required but missing (`"position_side is required for futures signal_orders strategies"`); 400 if `position_side` value is invalid (`"position_side must be 'long' or 'short'"`); 402 if insufficient credits; 409 if the authenticated user already has a strategy with the same name.

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
    "market_type": "spot",
    "signal_mode": "signal_orders",
    "timeframe": "4h",
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

**Errors:** 400 missing strategy name, 403 not owner, 404 not found.

### Edit Strategy

`POST /user?request_type=strategy_edit`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Existing strategy you own |
| `entry_condition` | string | No | New entry condition |
| `tp_condition` | string | No | New take profit |
| `sl_condition` | string | No | New stop loss |

:::{warning}
Editing a strategy creates a new version and triggers AI code regeneration. All marketplace subscribers of this strategy will be automatically unsubscribed.
:::

**Example body:**
```json
{"strategy_name": "emacross", "entry_condition": "EMA 12 crosses above EMA 26", "tp_condition": "Price reaches +5%", "sl_condition": "Price drops -3%"}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "version": 3, "status": "generating", "copiers_cancelled": true}}
```

### Set Strategy Visibility

`POST /user?request_type=strategy_visibility`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | |
| `visibility` | string | Yes | `"private"` or `"public"` |
| `credits_per_signal` | number | Yes* | 0.01-10 (*required for public) - fee charged to subscribers per signal |
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

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "current_version": 3, "versions": [{"version": 1, "created_at": 1784000000}, {"version": 2, "created_at": 1784500000}, {"version": 3, "created_at": 1784900000}]}}
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
- 403: authenticated user is not the owner
- 404: strategy not found
- 409: active marketplace listing must be unpublished first
- 503: the deletion could not be completed safely; nothing was deleted

---

## Backtest

**Endpoint:** `POST /backtest?action=<action>`

**Two backtest modes available:**
- **Specified Range** (`action=run`): Test a strategy on a specific date range for a single instrument.
- **Full Range** (`action=full_range`): Test a strategy on all available data for multiple instruments. Required for marketplace publishing.

Backtest requests remain backward compatible with the original crypto fields:
`coin` and `coins` still mean Binance-style crypto symbols such as `BTC`.
For non-crypto datasets, send instrument metadata alongside the legacy field:
`symbol` (for example `AAPL`, `EURUSD`, `XAUUSD`), `asset_class`
(`crypto`, `stock`, `etf`, `forex`, `index`, `commodity`), `provider`,
`market`, and optionally `exchange`. The service reads partitioned candles from
the matching `provider/market/symbol/timeframe` dataset when present and falls
back to the legacy `DATAS/{COIN}USDT_{TIMEFRAME}.txt` files for crypto.

### Estimate Cost

`POST /backtest?action=estimate`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `coins` | string[] | Yes |
| `timeframe` | string | Yes |
| `symbol` | string | No | Single-instrument estimate; legacy crypto callers can omit |
| `asset_class` | string | No | Defaults to `crypto` |
| `provider` | string | No | Defaults to `binance` |
| `market` | string | No | Defaults to `spot` |
| `exchange` | string | No | Optional venue label |

**Response:**
```json
{"action": "estimate", "total_candles": 6527547, "estimated_cost_credits": 0.35, "estimated_duration_seconds": 31, "chunks": 14, "current_credits": 7.35, "can_afford": true}
```

### Get Instrument Backtest Info

`POST /backtest?action=info`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `coin` | string | Yes* |
| `symbol` | string | No | Required for non-crypto instruments when `coin` is only a display label |
| `timeframe` | string | Yes |
| `asset_class` / `provider` / `market` / `exchange` | string | No |

**Response:**
```json
{"action": "info", "coin": "BTC", "symbol": "BTCUSDT", "instrument": {"asset_class": "crypto", "provider": "binance", "market": "spot", "symbol": "BTCUSDT"}, "timeframe": "4h", "data_range": {"first_ts": 1514764800, "last_ts": 1784476800, "first_date": "2018-01-01", "last_date": "2026-07-19", "total_candles": 21837}, "strategy": {"slug": "emacross", "candle_count": 32}, "cost_preview": {"credits_if_full": 0.05}, "current_credits": 7.35}
```

### List Available Timeframes

`POST /backtest?action=list_timeframes`

| Field | Type | Required |
|-------|------|----------|
| `coin` | string | Yes* |
| `symbol` | string | No |
| `asset_class` / `provider` / `market` / `exchange` | string | No |

**Response:**
```json
{"action": "list_timeframes", "coin": "BTC", "symbol": "BTCUSDT", "timeframes": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]}
```

### Run Specified Range Backtest

`POST /backtest?action=run`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `strategy_name` | string | Yes | | Strategy to test |
| `coin` | string | Yes* | | Backward-compatible display symbol, e.g. `"BTC"` |
| `symbol` | string | No | | Tradable/data symbol, e.g. `"BTCUSDT"`, `"AAPL"`, `"EURUSD"` |
| `asset_class` | string | No | `crypto` | `crypto`, `stock`, `etf`, `forex`, `index`, `commodity` |
| `provider` | string | No | `binance` | Data provider namespace |
| `market` | string | No | `spot` | Dataset market namespace |
| `exchange` | string | No | provider | Venue label |
| `timeframe` | string | Yes | | e.g. `"4h"` |
| `start_ts` | number | Yes | | Start unix timestamp |
| `end_ts` | number | Yes | | End unix timestamp |
| `commission` | number | No | 0.2 | Commission % |
| `position_pct` | number | No | 100 | Position size % |
| `min_gap_candles` | number | No | 4 | Min candles between signals |
| `max_wait_days` | number | No | 30 | Max days to wait for fill |
| `min_profit_pct` | number | No | 0.1 | Min profit target % |
| `max_profit_pct` | number | No | 30 | Max profit target % |
| `min_loss_pct` | number | No | 0.1 | Min stop loss % |
| `max_loss_pct` | number | No | 50 | Max stop loss % |
| `signal_filter_mode` | string | No | `"clamp"` | `"clamp"` (adjust to limits) or `"reject"` (skip signal) |

**Notes:**
- **Spread** is automatically determined by crypto coin volume tier for legacy Binance crypto. Non-crypto datasets currently use the default low-volume fallback unless the backend is extended with asset-class-specific spread rules.
- **signal_filter_mode = "clamp"** (default): If strategy TP exceeds `max_profit_pct`, it's clamped to max. If SL exceeds `max_loss_pct`, clamped to max. Signals below `min_profit_pct` are always skipped.
- **signal_filter_mode = "reject"**: Signals that exceed any min/max limit are completely skipped.
- **min/max profit/loss** values are passed to the strategy function as ratio parameters (`min_profit_ratio`, `max_profit_ratio`, `max_loss_ratio`, `min_loss_ratio`) for TP/SL price calculation.

**Response:**
```json
{"action": "run", "mode": "async_chunked", "job_id": "1784936800_6a2326", "cost_credits": 0.05, "remaining_credits": 7.30, "chunks": 1, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=1784936800_6a2326", "result": "?action=result&job_id=1784936800_6a2326"}}
```

### Full Range Backtest (for Marketplace)

`POST /backtest?action=full_range`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `coins` | string[] | Yes |
| `timeframe` | string | Yes |
| `asset_class` / `provider` / `market` / `exchange` | string | No |

Each requested instrument runs as a separate chunk. Required for `marketplace_publish` with `signal_mode=signal_orders`.

**Example body:**
```json
{"strategy_name": "emacross", "coins": ["BTC", "ETH", "SOL"], "timeframe": "4h"}
```

**Response:**
```json
{"action": "full_range", "job_id": "1784936800_fr_abc", "coins": ["BTC", "ETH", "SOL"], "chunks": 3, "cost_credits": 0.15, "remaining_credits": 7.20, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=1784936800_fr_abc", "result": "?action=result&job_id=1784936800_fr_abc"}}
```

### Launch Portfolio Backtest

`POST /backtest?action=portfolio`

Simulates all selected coins against **one shared balance**. The balance is
split into `divide` position slots: each position uses
`current balance / divide`, at most `divide` positions are open at once, and
at most one position per coin at a time. Signals that arrive with no free
slot are skipped (and counted). Commission and per-coin spread are applied
exactly as in single-coin runs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | |
| `coins` | string[] | Yes | 2–50 legacy coin/instrument labels |
| `asset_class` / `provider` / `market` / `exchange` | string | No | Shared dataset namespace for the selected instruments |
| `timeframe` | string | Yes | |
| `divide` | integer | No | 1–20; default = number of coins (capped at 20) |
| `initial_balance` | number | No | Default 100 |
| `commission` | number | No | Percent, default 0.2 |
| `start_ts` / `end_ts` | integer | No | Unix seconds; omitted = full history. Each coin is clipped to its own available range |

**Example body:**
```json
{"strategy_name": "emacross", "coins": ["BTC", "ETH", "SOL"], "timeframe": "4h", "divide": 3, "initial_balance": 100}
```

**Response:**
```json
{"action": "portfolio", "job_id": "pf_1784936800_ab12cd", "coins": ["BTC", "ETH", "SOL"], "divide": 3, "initial_balance": 100, "chunks": 3, "cost_credits": 0.25, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=pf_1784936800_ab12cd", "result": "?action=result&job_id=pf_1784936800_ab12cd"}}
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
{"job_id": "...", "status": "running", "progress_pct": 65, "elapsed_seconds": 42, "estimated_remaining_seconds": 22}
```

**Response (failed):**
```json
{"job_id": "...", "status": "failed", "progress_pct": 65, "elapsed_seconds": 42, "estimated_remaining_seconds": 0, "error": "Backtest execution failed"}
```

Failed-job credit recovery is automatic and is not a customer endpoint. The
status response contains only the customer-visible job state.

Status values: `running`, `completed`, `failed`

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
  "total_positions": 15, "total_trades": 7, "cost_credits": 0.05
}
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
{"ok": true, "data": {"backtests": [{"job_id": "...", "strategy_name": "emacross", "coin": "BTC", "timeframe": "4h", "cost_credits": 0.05, "created_at": 1784936800, "summary": {"total_trades": 7, "win_rate": 71.43, "total_return_pct": 5.46}}], "count": 1, "last_evaluated_key": "base64...", "has_more": true}}
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

Authentication is required. The caller identity is tracked for rate limiting,
audit and entitlement checks.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `market_type` | string | `"spot"` or `"futures"` |
| `timeframe` | string | e.g. `"4h"` |
| `coin` | string | Filter by one listed coin |
| `limit` | number | Default 50, min 1, max 100 |
| `cursor` | string | Opaque cursor returned by the previous page |

**Response:**
```json
{"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "owner": "MT***A", "market_type": "spot", "timeframe": "4h", "signal_mode": "signal_orders", "listed_coins": ["BTC", "ETH"], "signal_price_credits": 0.5, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "subscriber_count": 5, "total_signals_delivered": 42}], "next_cursor": "base64...", "has_more": true}
```

Send the returned cursor unchanged to fetch the next page. `has_more=false`
and a null cursor identify the final page. Malformed cursors and non-integer
page sizes return HTTP 400 instead of silently restarting at page one.

### Listing Detail

`GET /tradingdata?request_type=marketplace_listing&listing_id=lst_abc123`

Authentication is required. The response masks unrelated owner data and returns
caller-specific ownership and subscription state when applicable.

For the authenticated caller's ownership and subscription state, use:

`POST /user?request_type=marketplace_listing_detail`

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
    "timeframe": "4h",
    "leverage": 1,
    "signal_mode": "signal_orders",
    "listed_coins": ["BTC", "ETH"],
    "signal_price_credits": 0.5,
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
{"ok": true, "data": {"subscription_id": "sub_5c9f...", "listing_id": "lst_abc123", "strategy_name": "emacross", "active_coins": ["BTC", "ETH"], "signal_price_credits": 0.5, "bindings_created": 2}}
```

The subscription ID is deterministic for the authenticated user and listing.
The subscription is all-or-nothing; a failed request leaves no partial
subscription.

**Errors:** 403 license expired or active-strategy plan limit, 400 invalid coins / coin limit / self-subscribe, 409 duplicate subscription or binding conflict, 503 atomic commit unavailable.

### Unsubscribe

`POST /user?request_type=marketplace_unsubscribe`

| Field | Type | Required |
|-------|------|----------|
| `subscription_id` | string | Yes |

**Response:**
```json
{"ok": true, "data": {"status": "cancelled", "subscription_id": "sub_xyz789", "bindings_removed": 2}}
```

### My Listings

`POST /user?request_type=marketplace_my_listings`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"ok": true, "data": {"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "status": "active", "signal_mode": "signal_orders", "market_type": "spot", "timeframe": "4h", "listed_coins": ["BTC"], "signal_price_credits": 0.5, "subscriber_count": 5, "total_signals_delivered": 42, "total_credits_earned": 21.0, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "created_at": 1784000000}], "last_evaluated_key": "base64...", "has_more": true}}
```

### My Subscriptions

`POST /user?request_type=marketplace_my_subscriptions`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_size` | integer | No | Default 25, min 1, max 100 |
| `last_evaluated_key` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"ok": true, "data": {"subscriptions": [{"subscription_id": "sub_xyz789", "listing_id": "lst_abc123", "creator_beyin_id": "ABC123", "selected_coins": ["BTC"], "status": "active", "signal_price_credits": 0.5, "signals_received": 12, "credits_spent": 6.0, "created_at": 1784000000}], "last_evaluated_key": "base64...", "has_more": true}}
```

For both account lists, return the cursor unchanged to fetch the next result
page. Malformed cursors and non-integer page sizes return HTTP 400.

### Publish Strategy

`POST /user?request_type=marketplace_publish`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_key` | string | Yes | Lowercase alphanumeric |
| `description` | string | No | Max 500 chars, no HTML |
| `credits_per_signal` | number | Yes | 0.01 - 100.0 |
| `signal_mode` | string | Yes | `"signal_orders"` or `"signal_only"` |
| `requested_coins` | string[] | Yes | Coins to list |

:::{warning}
Requirements for `signal_mode=signal_orders`: Must have a successful `full_range` backtest. Only coins with positive PnL and at least 10 trades are listed. Others are rejected.
:::

Marketplace listing names are globally disambiguated by appending the creator's
Beyin ID to the user's local strategy name. For example, a local strategy named
`test1` owned by `ABC123` is listed as `test1_ABC123`. Other users may still
create their own local `test1` strategy.

**Example body:**
```json
{"strategy_key": "emacross", "description": "EMA crossover for BTC", "credits_per_signal": 0.5, "signal_mode": "signal_orders", "requested_coins": ["BTC", "ETH", "SOL"]}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "strategy_name": "emacross_ABC123", "display_strategy_name": "emacross", "status": "active", "listed_coins": ["BTC", "ETH"], "rejected_coins": {"SOL": "negative_pnl", "DOGE": "insufficient_trades"}, "credits_per_signal": 0.5, "signal_mode": "signal_orders", "backtest_summary": {"BTC": {"pnl_pct": 12.5, "win_rate": 68.0, "trades": 42}}}}
```

**Errors:** 400 no full_range backtest found, 400 no profitable coins.

### Update Listing

`POST /user?request_type=marketplace_update_listing`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing_id` | string | Yes | |
| `credits_per_signal` | number | No | 0.01 - 100.0 |
| `description` | string | No | Max 500 chars |

:::{danger}
Price change cancels ALL active subscriptions and removes bindings.
:::

**Example body:**
```json
{"listing_id": "lst_abc123", "credits_per_signal": 1.0, "description": "Updated description"}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "updated_fields": ["credits_per_signal"], "subscriptions_cancelled": 3, "note": "Price changed 0.5 -> 1.0. All subscriptions cancelled."}}
```

### Unpublish Listing

`POST /user?request_type=marketplace_unpublish`

| Field | Type | Required |
|-------|------|----------|
| `listing_id` | string | Yes |

:::{warning}
Cancels all subscriptions, removes bindings, sets status to "removed".
:::

**Response:**
```json
{"ok": true, "data": {"status": "removed", "subscriptions_cancelled": 5, "bindings_removed": 12}}
```

### Submit Review

`POST /user?request_type=marketplace_review`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing_id` | string | Yes | |
| `rating` | number | Yes | 1-5 |
| `comment` | string | No | Max 500 chars |

:::{note}
Must have (or had) a subscription to review. One review per user per listing. Cannot review own listing.
:::

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

Authentication is required. The caller identity is tracked for rate limiting,
audit and entitlement checks.

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

Authentication is required for every Trading Data request. Some responses may
still be license-gated by plan after the caller is identified.

### Trend Signals

`GET /tradingdata?request_type=trend_signals&page=0&limit=10`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | number | No | Page number (default 0). Page > 0 requires license. |
| `limit` | number | No | Items per page (default 10, max 10) |

**Response:**
```json
{"items": [{"coin_name": "BTC", "graph_type": "4h", "timestamp": "1784900000", "way": "BUY", "is_return_to_trend": false}], "page": 0, "count": 10, "last_page": false}
```

Collection items are lightweight discovery records. Clients must not rely on
`klines_data` in this response; request the selected signal through
`trend_signal_detail` when rendering its chart.

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
stops it at the break candle.

`klines_data` is the signal snapshot used to render the historical chart. A
detail response intended for the Trend Break history UI must include the full
signal snapshot returned by the API. Storage-only fields and internal links are
not part of the public response contract.

### Market Ticker

`GET /tradingdata?request_type=market_ticker&market=spot&page=0&limit=500`

Returns the market list used by the official app. Clients must call this Beyin
Finance API endpoint; they must not call exchange ticker endpoints directly.
The API filters ticker rows through server-maintained exchange metadata so only
symbols currently enabled for trading in the selected market are returned.

Price and quantity precision metadata may exist server-side for symbols that
are not currently trading, but those symbols are excluded from this ticker
catalog until they become trading-enabled again.

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
does not submit orders and does not require user Binance credentials, but the
API caller must still be authenticated and tracked.

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

### Market Sentiment

`GET /tradingdata?request_type=trend_indicator&market_key=BTCUSDT%231h`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `market_key` | string | No | Format: `SYMBOL#timeframe` (default: `BTCUSDT#1h`) |

**Response:**
```json
{"market_key": "BTCUSDT#1h", "item": {"market_key": "BTCUSDT#1h", "timestamp": 1784900000, "sentiment_score": 72, "trend": "BULLISH", "volatility": "MEDIUM"}, "count": 1}
```

### Sentiment History

`GET /tradingdata?request_type=trend_indicator_history&market_key=BTCUSDT%231h&limit=50`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `market_key` | string | No | Default: `BTCUSDT#1h` |
| `limit` | number | No | Max 200 (default 200) |
| `before_timestamp` | number | No | Pagination: get items before this timestamp |

**Response:**
```json
{"market_key": "BTCUSDT#1h", "items": [{"timestamp": 1784900000, "sentiment_score": 72, "trend": "BULLISH"}], "count": 50, "limit": 50, "has_more": true, "oldest_timestamp": 1784720000, "next_before_timestamp": 1784720000}
```

---

## General Config & Platform Data

### Get Platform Config

`GET /`

Authentication is required. Returns platform metadata such as banners and
supported assets. Cache locally and ignore unknown fields.

**Response:**
```json
{
  "GENERAL": "general",
  "banner_urls": ["https://..."],
  "supported_coins": ["BTC", "ETH", "SOL"],
  "app_version": "2.0.0"
}
```

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

Authentication is required. Returns system announcements such as new features
and maintenance messages.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 20, max 50 |

**Response:**
```json
{"notifications": [{"title": "New Feature", "body": "Marketplace is now live!", "type": "announcement", "timestamp": 1784900000}], "count": 1}
```

---

## Community

### Global Chat - Send Message

`POST /user?request_type=community_chat_send`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Max 500 characters |

**Response:**
```json
{"ok": true, "data": {"msg_id": "1784990000_MTHG7A", "sort_key": "1784990000#1784990000_MTHG7A"}}
```

### Global Chat - History

`GET /tradingdata?request_type=community_chat&limit=50`

Authentication is required to read visible community messages. Use the returned
`next_cursor` as the `cursor` query parameter for the next page.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 50, max 100 |
| `cursor` | string | No | Cursor returned by the previous page |

**Response:**
```json
{"messages": [{"beyin_id": "MTHG7A", "message": "BTC looking bullish!", "created_at": "1784990000", "sort_key": "..."}], "count": 50, "has_more": true, "next_cursor": "1784980000#..."}
```

Pass `next_cursor` back as `cursor` to request the next page.
The cursor is `null` and `has_more=false` on the final page.

### Create Post (Leaders Only)

`POST /user?request_type=community_post_create`

Only users with `community_role: "leader"` can create posts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Post title |
| `content` | string | Yes | Max 5000 characters |
| `image_url` | string | No | HTTPS URL for the attached image |

**Response:**
```json
{"ok": true, "data": {"post_id": "post_MTHG7A_1784990000"}}
```

Followers are automatically notified through their configured channels.

### List Posts

`GET /tradingdata?request_type=community_posts&limit=20`

Authentication is required to read visible leader posts. Pagination uses the
opaque `next_cursor` response value as the next request's `cursor`.

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
{"ok": true, "data": {"post_id": "...", "action": "commented"}}
```

### Report Content

`POST /user?request_type=community_post_report`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `post_id` | string | Conditional | For reporting a post |
| `type` | string | No | `"post"` (default) or `"chat"` |
| `sort_key` | string | Conditional | For reporting a chat message |

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

### Apply to Become Leader

`POST /user?request_type=community_leader_apply`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Why you want to be a leader (max 1000 chars) |
| `experience` | string | Yes | Your trading/crypto experience (max 2000 chars) |

**Response:**
```json
{"ok": true, "data": {"status": "pending", "message": "Application submitted. We will review and notify you."}}
```

**Errors:** 409 if already pending or already approved.

### List Leaders

`GET /tradingdata?request_type=community_leaders&limit=25`

Authentication is required. `is_following` is evaluated for the authenticated
caller; follow and unfollow actions use the `/user` endpoints.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | integer | No | Default 25, min 1, max 50 |
| `cursor` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"leaders": [{"beyin_id": "MTHG7A", "name": "CryptoTrader", "bio": "Full-time crypto analyst", "is_following": false}], "count": 1, "next_cursor": "base64...", "has_more": true}
```

Return the opaque cursor unchanged; malformed cursors return HTTP 400.

### Apply for Community Leader

`POST /user?request_type=community_leader_apply`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | Leader Display Name (3-30 Latin alphanumeric chars or spaces, e.g. `"Finans Kulubu"`) |
| `reason` | string | Yes | Reason for application (max 1000 chars) |
| `experience` | string | Yes | Trading experience details (max 2000 chars) |

The system automatically generates a unique lowercase nickname by removing spaces from `display_name` (e.g. `"Finans Kulubu"` -> `"finanskulubu"`). Returns 409 Conflict if nickname is already taken by another user.

**Response:**
```json
{
  "ok": true,
  "data": {
    "status": "pending",
    "display_name": "Finans Kulubu",
    "nickname": "finanskulubu",
    "message": "Application submitted. We will review and notify you."
  }
}
```

### Update Leader Profile

`POST /user?request_type=community_leader_update`

Only accessible by users with approved `"leader"` community role.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | New Leader Display Name (3-30 Latin alphanumeric chars or spaces) |
| `bio` | string | No | Updated bio / description |
| `avatar_url` | string | No | Optional new avatar image URL |

**Response:**
```json
{
  "ok": true,
  "data": {
    "display_name": "Finans Kulubu Pro",
    "nickname": "finanskulubupro",
    "community_bio": "Crypto & Forex specialist",
    "avatar_url": "https://..."
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
| 503 | A backing store the request needs is temporarily unavailable |

### Error `code` markers

`code` is optional. When present it identifies the class of authentication
failure so clients can react without parsing the message text.

| `code` | Meaning | Client action |
|--------|---------|---------------|
| `session_expired` | The session token itself was missing, invalid, or expired. | Clear the stored session and re-authenticate. |
| `invalid_credentials` | The Developer API key/secret was rejected or has been revoked. | Issue new API credentials. An authenticated app session is unaffected. |
| `api_key_store_unavailable` | The Developer API key store could not be reached, so no credential was evaluated. Always paired with HTTP 503. | Retry with backoff. Do not rotate credentials and do not clear the session. |

`api_key_store_unavailable` is the answer for a missing dependency, not a
rejected credential: it is never a 401 and never a bare 500. It applies to
`api_key_generate`, `api_key_list`, `api_key_revoke`, `X-API-Key` /
`X-API-Secret` authentication on `/user`, and the same header pair on
`/tradingdata`. The response body stays generic — no table, resource, or
internal error detail is exposed.

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
| Binance API key or secret is not exactly 64 characters (`"Invalid API or Secret key"`) | 400 |
| Binance returned no account ID while linking (`"Could not retrieve Binance ID from API"`) | 502 |
| Login with a Binance identity that is not registered (`"Binance ID not found!"`) | 400 |
| Login where the supplied Google identity does not match the stored one (`"Google ID mismatch!"`) | 409 |

None of these responses carry a `code` marker.


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

Response items use the same schema as `trend_signals` — full signal data including klines and trend lines. Internal fields (`gsi_pk`, `ttl`, `telegram_link`, `tracked_users`) are stripped from the response.

**Errors:**
- 401: Authentication required (`"code": "session_expired"`)
