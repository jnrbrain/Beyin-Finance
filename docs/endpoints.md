# Beyin Finance Developer API Reference

**Base URL:** `https://08rxd1g3ik.execute-api.eu-central-1.amazonaws.com/BeyinAPI`

---

## Authentication

Use developer API credentials for authenticated integrations. Do not send
credentials to public routes unless the endpoint explicitly requires them.

| Client | Authentication |
|--------|----------------|
| Developer/integration client | `X-API-Key` + `X-API-Secret` |
| Public Trading Data routes | No authentication unless the route says otherwise |

**Developer API-key example:**

```
X-API-Key: bf_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
X-API-Secret: bf_sec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

Generate API keys from the Telegram bot, web dashboard, or mobile app.

A missing or invalid developer credential returns HTTP 401.
Unless an endpoint is explicitly marked “No auth required,” every `/user` and
`/backtest` operation in this reference requires the developer headers above.

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
Retry-After: 23               # Seconds until reset
```

### Client Best Practices

- Read `X-RateLimit-Remaining` from every response
- If `Remaining` < 5, slow down or queue requests
- On 429, wait `Retry-After` seconds before retrying
- Cache responses when possible (e.g. `account_info`, `available_coins`)

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
        "order_history_id": "order#oco#BF-123#...",
        "timestamp": 1784936800,
        "strategy_name": "emacross",
        "coin": "BTC",
        "exchange_order_status": "NEW",
        "execution_mode": "real_trade",
        "order_source": "signal",
        "signal_position_key": "emacross#BTC#1784850000"
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
exchange order. The API applies Binance price/quantity precision, validates
TP/SL direction, checks the current minimum-notional rule and verifies the
authenticated Binance Spot account's immediately available balance before
returning the irreversible-operation summary. OCO is currently supported for
Spot only. A successful preview is not a balance reservation; execution repeats
the check because the balance can change concurrently.

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
    "signal_position_key": "emacross#BTC#1784850000",
    "irreversible": true
  }
}
```

The client must obtain a successful preview and require explicit user
confirmation before calling `binance_order`.

### Place Binance OCO Order

`POST /user?request_type=binance_order`

Places an OCO (One-Cancels-Other) order on Binance. Combines a Take-Profit limit order and a Stop-Loss stop-limit order. When one triggers, the other is automatically cancelled.

Requires Binance API keys linked.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | e.g. `"BTCUSDT"` |
| `side` | string | Yes | `"BUY"` or `"SELL"` — your entry side (OCO exit side is inverted) |
| `quantity` | number | Yes | Amount to sell/buy when TP or SL triggers |
| `entry_price` | number | No | Optional reference entry price |
| `take_profit_price` | number | Yes | Take-profit limit price |
| `stop_loss_price` | number | Yes | Stop-loss trigger price |
| `market_type` | string | No | `"spot"` (default). Futures OCO is currently rejected. |
| `order_source` | string | Yes | `"signal"` when entering an active Signal + Orders signal; `"independent"` for an order not linked to a signal |
| `signal_order_id` | string | Conditional | Optional signal identifier; forbidden for independent orders |
| `signal_position_key` | string | Conditional | Required for `order_source=signal`; forbidden for independent orders |
| `idempotency_key` | string | Yes | 16-128 letters, numbers, `_` or `-`; generate before preview and reuse for every retry |

:::{note}
- Prices and quantities are automatically formatted to Binance precision requirements (from `binanceExchangeInfo.json`)
- During preview and immediately before a real submission, the API checks the authenticated
  Binance Spot account. A SELL OCO requires enough free base asset; a BUY OCO
  requires enough free USDT for the highest order leg. Binance remains the
  final authority because the balance can change concurrently.
- The OCO exit side is automatically determined: if your entry `side` is `BUY` (long), exit is `SELL`
- The same idempotency key with a different normalized order payload returns HTTP 409.
- For `order_source=signal`, the API reads the authenticated
  user's active signal and accepts only `signal_mode=signal_orders`. The symbol
  and optional `signal_order_id` must match that record.
- Every accepted order records `order_source`; linked orders also record
  `signal_position_key` and `signal_order_id`.
:::

**Example body:**
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": 0.001,
  "entry_price": 65000,
  "take_profit_price": 67000,
  "stop_loss_price": 63000,
  "market_type": "spot",
  "order_source": "signal",
  "signal_position_key": "emacross#BTC#1784850000",
  "idempotency_key": "oco_1784990000000_a1b2c3d4e5f60708"
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "order_list_id": "12345678",
    "client_order_id": "BFOCO_MTHG7A_1784990000",
    "symbol": "BTCUSDT",
    "side": "SELL",
    "quantity": "0.00100",
    "take_profit_price": "67000.00",
    "stop_loss_price": "63000.00",
    "orders": [
      {"symbol": "BTCUSDT", "orderId": 111, "type": "LIMIT_MAKER"},
      {"symbol": "BTCUSDT", "orderId": 222, "type": "STOP_LOSS_LIMIT"}
    ],
    "signal_order_id": "",
    "signal_position_key": "emacross#BTC#1784850000",
    "order_source": "signal",
    "local_order_key": "oco#7c6c...",
    "idempotency_key": "oco_1784990000000_a1b2c3d4e5f60708",
    "status": "submitted"
  }
}
```

Repeating the same key and normalized payload after completion returns the
stored response with `idempotent_replay=true`; Binance is not called twice.

If Binance acceptance cannot be confirmed, the API conservatively returns HTTP
202 instead of declaring failure:

```json
{"ok": true, "data": {"status": "unknown_checking", "idempotency_key": "oco_1784990000000_a1b2c3d4e5f60708", "client_order_id": "BFOCO_MTHG7A_0123456789abcdef", "message": "Binance acceptance could not be confirmed; no duplicate was submitted"}}
```

The client must not create a new key or blindly resubmit in this state. It must
show `Unknown/Checking` and direct the user to Orders/Binance. The Binance
`listClientOrderId` is deterministically derived from the idempotency key.

**Errors:**
- 400: Missing/non-finite/non-numeric fields, invalid source/link combination, Futures market, precision/minimum-notional failure, insufficient available Spot balance, or invalid idempotency key
- 404: A linked active signal does not exist for the authenticated user
- 409: The key was reused with a different order, or the linked signal is not `signal_orders`/does not match the symbol
- 503: Binance balance or safe order submission could not be verified; the order was not submitted

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

---

## Economic News

### Get Economic News

`POST /user?request_type=economic_news`

**Cost:** 0.01 ⚡ per request

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

**Cost:** 0.01 ⚡ per request

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
| `strategy_name` | string | Yes | Unique, lowercase alphanumeric, min 4 chars, at least 1 letter (`^[a-z0-9]+$`) |
| `market_type` | string | Yes | `"spot"` or `"futures"` |
| `signal_mode` | string | Yes | `"signal_orders"` or `"signal_only"` |
| `timeframe` | string | Yes | `1m,3m,5m,15m,30m,1h,2h,4h,1d` |
| `entry_condition` | string | Yes | Entry condition in natural language |
| `tp_condition` | string | Yes* | Take profit (*required for signal_orders) |
| `sl_condition` | string | Yes* | Stop loss (*required for signal_orders) |

:::{note}
Strategies are always created as private. Use `strategy_visibility` to make public after a successful full_range backtest.
:::

**Cost:** 1.0 ⚡ total (0.05 upfront + 0.95 on success)

**Example body:**
```json
{"strategy_name": "emacross", "market_type": "spot", "signal_mode": "signal_orders", "timeframe": "4h", "entry_condition": "EMA 9 crosses above EMA 21", "tp_condition": "Price reaches +3%", "sl_condition": "Price drops -2%"}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "version": 1, "signal_mode": "signal_orders", "status": "generating", "cost_upfront": 0.05, "cost_on_success": 0.95}}
```

**Errors:** 400 name too short (min 4), 400 invalid characters, 400 must contain letter, 402 insufficient credits, 409 name taken.

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
| `credits_per_signal` | number | Yes* | 0.01-10 (*required for public) — fee charged to subscribers per signal |
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

⚠️ **Two backtest modes available:**
- **Specified Range** (`action=run`): Test a strategy on a specific date range for a single coin.
- **Full Range** (`action=full_range`): Test a strategy on all available data for multiple coins. Required for marketplace publishing.

### Estimate Cost

`POST /backtest?action=estimate`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `coins` | string[] | Yes |
| `timeframe` | string | Yes |

**Response:**
```json
{"action": "estimate", "total_candles": 6527547, "estimated_cost_credits": 0.35, "estimated_duration_seconds": 31, "chunks": 14, "current_credits": 7.35, "can_afford": true}
```

### Get Coin Backtest Info

`POST /backtest?action=info`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `coin` | string | Yes |
| `timeframe` | string | Yes |

**Response:**
```json
{"action": "info", "coin": "BTC", "timeframe": "4h", "data_range": {"first_ts": 1514764800, "last_ts": 1784476800, "first_date": "2018-01-01", "last_date": "2026-07-19", "total_candles": 21837}, "strategy": {"slug": "emacross", "candle_count": 32}, "cost_preview": {"credits_if_full": 0.05}, "current_credits": 7.35}
```

### List Available Timeframes

`POST /backtest?action=list_timeframes`

| Field | Type | Required |
|-------|------|----------|
| `coin` | string | Yes |

**Response:**
```json
{"action": "list_timeframes", "coin": "BTC", "timeframes": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]}
```

### Run Specified Range Backtest

`POST /backtest?action=run`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `strategy_name` | string | Yes | | Strategy to test |
| `coin` | string | Yes | | e.g. `"BTC"` |
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
- **Spread** is automatically determined by coin volume tier: High volume (BTC, ETH, SOL...) = 0%, Mid volume = 0.1%, Low volume = 0.2%. Not user-configurable.
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

Each coin runs as a separate chunk. Required for `marketplace_publish` with `signal_mode=signal_orders`.

**Example body:**
```json
{"strategy_name": "emacross", "coins": ["BTC", "ETH", "SOL"], "timeframe": "4h"}
```

**Response:**
```json
{"action": "full_range", "job_id": "1784936800_fr_abc", "coins": ["BTC", "ETH", "SOL"], "chunks": 3, "cost_credits": 0.15, "remaining_credits": 7.20, "status": "dispatched", "poll_actions": {"status": "?action=status&job_id=1784936800_fr_abc", "result": "?action=result&job_id=1784936800_fr_abc"}}
```

### Poll Status

`POST /backtest?action=status`

| Field | Type | Required |
|-------|------|----------|
| `job_id` | string | Yes |

**Response (running):**
```json
{"job_id": "...", "status": "running", "progress_pct": 65, "chunks_total": 14, "chunks_done": 9, "elapsed_seconds": 42, "estimated_remaining_seconds": 22}
```

**Response (failed):**
```json
{"job_id": "...", "status": "failed", "progress_pct": 65, "chunks_total": 14, "chunks_done": 9, "elapsed_seconds": 42, "estimated_remaining_seconds": 0, "error": "Backtest execution failed"}
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

No authentication is required.

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

No authentication is required. The public response masks the owner and returns
`is_owner: false`, an empty `subscription_status`, and an empty
`selected_coins` list.

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
Requirements for `signal_mode=signal_orders`: Must have a successful `full_range` backtest. Only coins with positive PnL and ≥10 trades are listed. Others are rejected.
:::

**Example body:**
```json
{"strategy_key": "emacross", "description": "EMA crossover for BTC", "credits_per_signal": 0.5, "signal_mode": "signal_orders", "requested_coins": ["BTC", "ETH", "SOL"]}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "status": "active", "listed_coins": ["BTC", "ETH"], "rejected_coins": {"SOL": "negative_pnl", "DOGE": "insufficient_trades"}, "credits_per_signal": 0.5, "signal_mode": "signal_orders", "backtest_summary": {"BTC": {"pnl_pct": 12.5, "win_rate": 68.0, "trades": 42}}}}
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

No authentication is required.

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

## Trading Data (Public)

Page 0 is public. Page > 0 requires valid license.

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

Collection items are lightweight discovery records. Candle and trend-line
arrays are intentionally omitted; request a specific signal through
`trend_signal_detail` when chart data is needed.

### Trend Signal Detail

`GET /tradingdata?request_type=trend_signal_detail&coin_name=BTC&graph_type=240&timestamp=1784900000`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `coin_name` | string | Yes | e.g. `"BTC"` |
| `graph_type` | string | Yes | Signal timeframe exactly as returned by the list, for example `"4h"` |
| `timestamp` | string | Yes | Signal timestamp |

**Response:**
```json
{"item": {"coin_name": "BTC", "graph_type": "4h", "timestamp": "1784900000", "way": "BUY", "is_return_to_trend": false, "trend_data": {"low_trend": [["1784800000000", 12, "67200.5"], ["1784900000000", 90, "68120.0"]]}, "klines_data": []}}
```

`trend_data` contains the calculated high/low trend-line points. Each point is
`[timestamp_ms, candle_index, price]`. `klines_data` is included only for
licensed users.

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

No auth required. Returns public platform metadata such as banners and supported assets. Cache locally and ignore unknown fields.

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

No auth required. Returns system announcements (new features, maintenance, etc.).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 20, max 50 |

**Response:**
```json
{"notifications": [{"title": "New Feature", "body": "Marketplace is now live!", "type": "announcement", "timestamp": 1784900000}], "count": 1}
```

---

## Community

### Global Chat — Send Message

`POST /user?request_type=community_chat_send`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Max 500 characters |

**Response:**
```json
{"ok": true, "data": {"msg_id": "1784990000_MTHG7A", "sort_key": "1784990000#1784990000_MTHG7A"}}
```

### Global Chat — History

`GET /tradingdata?request_type=community_chat&limit=50`

No authentication is required to read visible community messages. Use the
returned `next_cursor` as the `cursor` query parameter for the next page.

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

No authentication is required to read visible leader posts. Pagination uses
the opaque `next_cursor` response value as the next request's `cursor`.

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

No authentication is required. Anonymous results return `is_following: false`;
follow and unfollow actions still require authentication.

| Query parameter | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | integer | No | Default 25, min 1, max 50 |
| `cursor` | string | No | Opaque cursor returned by the previous page |

**Response:**
```json
{"leaders": [{"beyin_id": "MTHG7A", "name": "CryptoTrader", "bio": "Full-time crypto analyst", "is_following": false}], "count": 1, "next_cursor": "base64...", "has_more": true}
```

Return the opaque cursor unchanged; malformed cursors return HTTP 400.

---

## Errors

All errors return:
```json
{"error": "Descriptive error message"}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Invalid credentials / not registered |
| 402 | Insufficient credits |
| 403 | Forbidden / license expired |
| 404 | Not found |
| 405 | Invalid request_type |
| 409 | Conflict (duplicate) |
| 429 | Rate limited |
| 500 | Server error |

### Backtest estimate modes

`POST /backtest?action=estimate` accepts the common strategy, coin(s), and
timeframe fields. Without timestamps it estimates a multi-coin `full_range`
operation, including its success charge. When both `start_ts` and `end_ts` are
provided it estimates a single-coin `run`, clips the timestamps to available
data, and returns the range candle count and standard run cost. Supplying only
one timestamp, an inverted range, or multiple coins in range mode returns 400.
The response includes `mode`, either `full_range` or `range`.
