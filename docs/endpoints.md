# Beyin Finance Developer API Reference

**Base URL:** `https://08rxd1g3ik.execute-api.eu-central-1.amazonaws.com/BeyinAPI`

---

## Authentication

The API supports multiple authentication modes. Use the mode appropriate to the
client; do not send more credentials than the selected mode requires.

| Client | Authentication |
|--------|----------------|
| Mobile/Web first-party client | `Authorization: Bearer <JWT>` |
| Developer/integration client | `X-API-Key` + `X-API-Secret` |
| Legacy first-party client | Beyin ID/password contract, where still supported |
| Public Trading Data routes | No authentication unless the route says otherwise |

**JWT example:**

```
Authorization: Bearer eyJ...
Content-Type: application/json
```

**Developer API-key example:**

```
X-API-Key: bf_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
X-API-Secret: bf_sec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

Generate API keys from the Telegram bot, web dashboard, or mobile app.

The Backtest endpoint accepts JWT and retains the legacy password/API-key modes
for backward compatibility. A missing or invalid credential returns HTTP 401.

:::{warning}
The contracts added for the mobile client in this document are implemented in the
repository but remain **deployment pending** until the corresponding Lambda/API
Gateway changes are released to AWS. Clients must not assume a local contract is
available in production before the deployment checklist is completed.
:::

---

## Rate Limits

| Plan | Requests/min (API Key) | Requests/min (App/Web) |
|------|----------------------|----------------------|
| free | 30 | 60 |
| starter | 30 | 60 |
| plus | 60 | 120 |
| pro | 120 | 240 |
| investor | 240 | 480 |

App/Web requests (JWT or beyin_password auth) get 2× the limit.

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

### Implementation Details

- Rate limiting is **per user, per minute** (not per IP)
- Counters are stored in DynamoDB (atomic increment) — consistent across all Lambda instances
- Counters auto-expire 2 minutes after the window resets
- Telegram bot requests are **not rate limited**
- Internal endpoints (`position_tracker`) are **not rate limited**

### Client Best Practices

- Read `X-RateLimit-Remaining` from every response
- If `Remaining` < 5, slow down or queue requests
- On 429, wait `Retry-After` seconds before retrying
- Cache responses when possible (e.g. `account_info`, `available_coins`)

## Plan Limits

| Plan | Monthly | Annual (-50%) | Max Active Strategies | Max Coins/Strategy |
|------|---------|---------------|----------------------|-------------------|
| free | - | - | - | - |
| starter | 10 USDT | 60 USDT | 1 | 5 |
| plus | 20 USDT | 120 USDT | 2 | 15 |
| pro | 50 USDT | 300 USDT | 5 | 30 |
| investor | 100 USDT | 600 USDT | 10 | 200 |

:::{note}
**How to pay:** Send USDT via Binance Pay to ID `863 826 81`. 0% commission. Payment is processed automatically within 2 minutes.

- Minimum deposit: **1 USDT** (grants 1-month demo for free)
- You can send any amount — license duration is calculated based on the amount sent
- **50% discount** on 6-month and above payments (annual prices in table reflect this)
:::

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

### Get Credits History

`POST /user?request_type=credits_history`

Returns all credit deposits and spends for the current and previous month.

**Response:**
```json
{
  "ok": true,
  "data": {
    "transactions": [
      {"type": "spend", "amount": -0.05, "action": "backtest", "description": "Backtest cost 0.05", "timestamp": 1784936800},
      {"type": "spend", "amount": -0.01, "action": "economic_news", "description": "Economic news fetch", "timestamp": 1784936700},
      {"type": "deposit", "amount": 5.0, "action": "deposit", "description": "Payment abc12345", "timestamp": 1784900000}
    ],
    "count": 15
  }
}
```

**Transaction actions:** `deposit`, `backtest`, `backtest_refund`, `strategy_generate`, `strategy_success`, `economic_news`, `marketplace_signal`

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

Returns at most 100 records. Internal fields and stored exchange/credential
payloads are removed from the response.

**Response:**
```json
{
  "ok": true,
  "data": {
    "orders": [
      {
        "strategy_name": "emacross",
        "coin": "BTC",
        "exchange_order_status": "NEW",
        "execution_mode": "real_trade"
      }
    ],
    "count": 1,
    "status": "active"
  }
}
```

### Preview Binance OCO Order

`POST /user?request_type=binance_order_preview`

Uses the same request fields as `binance_order`, but does **not** place an
exchange order. The server applies Binance price/quantity precision, validates
TP/SL direction and checks the current minimum-notional rule before returning
the irreversible-operation summary.

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
    "irreversible": true
  }
}
```

The mobile client must obtain a successful preview and display an explicit
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
| `entry_price` | number | No | Reference entry price (for logging) |
| `take_profit_price` | number | Yes | Take-profit limit price |
| `stop_loss_price` | number | Yes | Stop-loss trigger price |
| `market_type` | string | No | `"spot"` (default) or `"futures"` |
| `signal_order_id` | string | No | Links to an existing signal record |
| `signal_position_key` | string | No | If provided, updates the opened signal with OCO info |

:::{note}
- Prices and quantities are automatically formatted to Binance precision requirements (from `binanceExchangeInfo.json`)
- The OCO exit side is automatically determined: if your entry `side` is `BUY` (long), exit is `SELL`
- Order is routed through the Lightsail proxy (statik IP: Frankfurt)
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
  "signal_position_key": "emacross#BTC#1784850000"
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
    "signal_position_key": "emacross#BTC#1784850000"
  }
}
```

**Errors:**
- 400: Missing/invalid fields
- 502: Binance rejected the order (insufficient balance, invalid price, etc.)

**Close reasons (tracked by position_tracker):**
| Reason | Description |
|--------|-------------|
| `TARGET` | Take-profit limit order filled |
| `STOP` | Stop-loss triggered and filled |
| `CANCELLED` | User manually cancelled on Binance |

### Get Notifications

`POST /user?request_type=notifications_list`

No body params. Returns last 100 notifications sorted newest first.

**Response:**
```json
{
  "ok": true,
  "data": {
    "notifications": [
      {"title": "Backtest Complete", "body": "Your BTC 4h backtest finished", "event_type": "backtest_complete", "timestamp": 1784900000}
    ],
    "count": 1
  }
}
```

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

### Delete Account

`POST /user?request_type=delete`

No body params. Schedules account for deletion after 30 days.

:::{warning}
Account is soft-deleted: disabled for 30 days, then permanently removed. Logging in within 30 days automatically restores the account. Credits and strategies are preserved during the grace period.
:::

**Response:**
```json
{"ok": true, "data": {"message": "Account scheduled for deletion", "deletion_scheduled_at": 1787500000, "recovery_until": 1787500000, "note": "Log in within 30 days to cancel deletion and restore your account."}}
```

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
credentials and internal storage metadata are not exposed.

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

The operation verifies ownership and marketplace state, then atomically removes
the user-visible strategy registry/binding state. Immutable strategy versions
and related backtest objects are subsequently cleaned up. If marketplace state
cannot be verified, deletion fails closed and no user-visible data is removed.

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "deleted": true, "deleted_objects": 8}}
```

**Errors:**

- 400: missing name or confirmation mismatch
- 403: authenticated user is not the owner
- 404: strategy not found
- 409: active marketplace listing must be unpublished first
- 503: marketplace state could not be verified; nothing was deleted

---

## Backtest

**Endpoint:** `POST /backtest?action=<action>`

⚠️ **Two backtest modes available:**
- **Specified Range** (`action=run`): Test a strategy on a specific date range for a single coin.
- **Full Range** (`action=full_range`): Test a strategy on all available data for multiple coins. Required for marketplace publishing.

:::{note}
Failed jobs are automatically refunded.
:::

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

**Response (failed — auto-refunded):**
```json
{"job_id": "...", "status": "failed", "error": "Strategy execution error", "refunded_credits": 0.05}
```

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
  "all_positions": [...], "trades": [...],
  "total_positions": 15, "total_trades": 7, "cost_credits": 0.05
}
```

### Refund Failed Backtest

`POST /backtest?action=result_refund`

| Field | Type | Required |
|-------|------|----------|
| `job_id` | string | Yes |

Only a job whose persisted progress state is `failed` can be refunded. Refund
state is persisted so a repeated request returns the existing result rather than
issuing a second credit.

**First successful response:**
```json
{"action": "result_refund", "job_id": "1784936800_6a2326", "refunded_credits": 0.05, "status": "refunded"}
```

**Repeated response:**
```json
{"action": "result_refund", "job_id": "1784936800_6a2326", "refunded_credits": 0.05, "status": "refunded", "already_refunded": true}
```

**Errors:** 400 job is not failed, 404 job/progress/manifest not found.

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

**Example body:**
```json
{"strategy_name": "emacross", "coin": "BTC", "timeframe": "4h"}
```

**Response:**
```json
{"ok": true, "data": {"backtests": [{"job_id": "...", "strategy_name": "emacross", "coin": "BTC", "timeframe": "4h", "cost_credits": 0.05, "summary": {"total_trades": 7, "win_rate": 71.43, "total_return_pct": 5.46}}], "count": 50}}
```

---

## Signals

### Active Signals

`POST /user?request_type=active_signals`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string or string[] | No | Filter by strategy. Single string or array. Omit for all signals. |

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
{"ok": true, "data": {"signals": [{"position_key": "emacross#BTC#1784850000", "coin": "BTC", "strategy_name": "emacross", "owner": "MTHG7A", "side": "LONG", "signal_mode": "signal_orders", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "source": "user", "created_at": 1784850000}], "count": 1}}
```

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
{"ok": true, "data": {"signals": [{"closed_key": "...", "coin": "BTC", "strategy_name": "emacross", "side": "LONG", "signal_mode": "signal_orders", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "exit_price": "69500.00", "result": "GAIN", "source": "user", "created_at": 1784850000, "closed_at": 1784950000}], "last_evaluated_key": "base64..."}}
```

---

## Automated Trading

:::{warning} This feature is currently unavailable. It will be integrated and made available once the SPK (Capital Markets Board) license is obtained. The following endpoints are currently disabled.
:::

All automated trading endpoints return the same structure with `bot_settings`, `limits`, `counts`, `catalog`, and `sync` fields.

### Get Status

> **⚠️ This endpoint is currently disabled.**

`POST /user?request_type=automated_trading_status`

No body params.

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 100, "strategy_configs": {"emacross": {"key": "emacross", "name": "emacross", "source": "user", "enabled": true, "coins": ["BTC", "ETH"]}}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 2, "user_strategies": 1, "system_strategies": 1},
  "catalog": [{"key": "emacross", "name": "emacross", "source": "user", "coins": []}],
  "sync": {"bindings_created": 0, "bindings_removed": 0}
}
```

### Update Automated Trading Settings

> **⚠️ This endpoint is currently disabled.**

`POST /user?request_type=automated_trading_update`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `automated_trading_enabled` | boolean | No | Enable/disable all trading |
| `allocation_pct` | number | No | 0-100, global allocation % |

**Example body:**
```json
{"automated_trading_enabled": true, "allocation_pct": 80}
```

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 80, "strategy_configs": {...}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 2, "user_strategies": 1, "system_strategies": 1},
  "catalog": [...],
  "sync": {"bindings_created": 0, "bindings_removed": 0}
}
```

### Add Strategy

> **⚠️ This endpoint is currently disabled.**

`POST /user?request_type=automated_strategy_add`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_key` | string | Yes | Strategy name from catalog |
| `coins` | string | No | Comma-separated coin list (e.g. `"BTC,ETH,SOL"`) |
| `enabled` | boolean | No | Default: true |

**Example body:**
```json
{"strategy_key": "emacross", "coins": "BTC,ETH,SOL", "enabled": true}
```

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 100, "strategy_configs": {"emacross": {"key": "emacross", "name": "emacross", "source": "user", "enabled": true, "coins": ["BTC", "ETH", "SOL"]}}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 1, "user_strategies": 1, "system_strategies": 0},
  "catalog": [...],
  "sync": {"bindings_created": 3, "bindings_removed": 0},
  "ignored_invalid": [],
  "ignored_over_limit": []
}
```

**Errors:**
- 404: `"Strategy not found"` — strategy_key doesn't exist in your catalog
- 409: `"Strategy already configured"` — already added
- 400: `"Max N active strategies allowed for your plan"` — plan limit reached

### Remove Strategy

> **⚠️ This endpoint is currently disabled.**

`POST /user?request_type=automated_strategy_remove`

| Field | Type | Required |
|-------|------|----------|
| `strategy_key` | string | Yes |

**Example body:**
```json
{"strategy_key": "emacross"}
```

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 100, "strategy_configs": {}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 0, "user_strategies": 0, "system_strategies": 0},
  "catalog": [...],
  "sync": {"bindings_created": 0, "bindings_removed": 3}
}
```

**Errors:** 404 strategy not configured.

### Set Strategy Coins

> **⚠️ This endpoint is currently disabled.**

`POST /user?request_type=automated_strategy_set_coins`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_key` | string | Yes | |
| `coins` | string | Yes | Comma-separated (e.g. `"BTC,ETH,SOL"`) |

**Example body:**
```json
{"strategy_key": "emacross", "coins": "BTC,SOL"}
```

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 100, "strategy_configs": {"emacross": {"key": "emacross", "enabled": true, "coins": ["BTC", "SOL"]}}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 1, "user_strategies": 1, "system_strategies": 0},
  "catalog": [...],
  "sync": {"bindings_created": 1, "bindings_removed": 1},
  "ignored_invalid": [],
  "ignored_over_limit": []
}
```

**Errors:** 400 system strategy (coins managed by server), 404 not configured.

### Toggle Strategy

> **⚠️ This endpoint is currently disabled.**

`POST /user?request_type=automated_strategy_toggle`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_key` | string | Yes | |
| `enabled` | boolean | No | If omitted, toggles current state |

**Example body:**
```json
{"strategy_key": "emacross", "enabled": false}
```

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 100, "strategy_configs": {"emacross": {"key": "emacross", "enabled": false, "coins": ["BTC", "ETH"]}}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 1, "user_strategies": 1, "system_strategies": 0},
  "catalog": [...],
  "sync": {"bindings_created": 0, "bindings_removed": 2}
}
```

**Errors:** 404 strategy not configured.

---

## Marketplace

### Browse Listings

`POST /user?request_type=marketplace_browse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filters` | object | No | Filter object (see below) |
| `page_size` | number | No | Default 50, max 500 |
| `last_evaluated_key` | string | No | Pagination cursor (base64) from previous response |

**Filter object fields:**

| Field | Type | Description |
|-------|------|-------------|
| `market_type` | string | `"spot"` or `"futures"` |
| `timeframe` | string | e.g. `"4h"` |
| `signal_mode` | string | `"signal_orders"` or `"signal_only"` |
| `min_win_rate` | number | Min win rate % |
| `coins` | string[] | Filter by listed coins |

**Example body:**
```json
{"filters": {"market_type": "spot", "min_win_rate": 55, "coins": ["BTC"]}, "page_size": 100}
```

**Response:**
```json
{"ok": true, "data": {"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "owner": "MT***A", "market_type": "spot", "timeframe": "4h", "signal_mode": "signal_orders", "listed_coins": ["BTC", "ETH"], "credits_per_signal": 0.5, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "subscriber_count": 5, "total_signals_delivered": 42}], "last_evaluated_key": "base64..."}}
```

### Listing Detail

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
    "credits_per_signal": 0.5,
    "total_pnl_pct": 12.5,
    "win_rate_pct": 68.0,
    "subscriber_count": 5,
    "total_signals_delivered": 42,
    "avg_rating": 4.2,
    "review_count": 8,
    "created_at": 1784000000
  }
}
```

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
{"ok": true, "data": {"subscription_id": "sub_xyz789", "listing_id": "lst_abc123", "strategy_name": "emacross", "active_coins": ["BTC", "ETH"], "credits_per_signal": 0.5, "bindings_created": 2}}
```

**Errors:** 403 license expired, 400 invalid coins / plan limit / self-subscribe.

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

No body params.

**Response:**
```json
{"ok": true, "data": {"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "status": "active", "signal_mode": "signal_orders", "market_type": "spot", "timeframe": "4h", "listed_coins": ["BTC"], "credits_per_signal": 0.5, "subscriber_count": 5, "total_signals_delivered": 42, "total_credits_earned": 21.0, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "created_at": 1784000000}]}}
```

### My Subscriptions

`POST /user?request_type=marketplace_my_subscriptions`

No body params.

**Response:**
```json
{"ok": true, "data": {"subscriptions": [{"subscription_id": "sub_xyz789", "listing_id": "lst_abc123", "creator_beyin_id": "ABC123", "selected_coins": ["BTC"], "status": "active", "credits_per_signal": 0.5, "signals_received": 12, "credits_spent": 6.0, "created_at": 1784000000}]}}
```

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

`POST /user?request_type=marketplace_reviews`

| Field | Type | Required |
|-------|------|----------|
| `listing_id` | string | Yes |
| `limit` | number | No | Default 20, max 50 |

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "reviews": [{"beyin_id": "MT***A", "rating": 5, "comment": "Great strategy!", "timestamp": 1784900000}], "count": 3}}
```

---

## Trading Data (Public)

Page 0 is public. Page > 0 requires valid license.

### Market Ticker

`GET /tradingdata?request_type=market_ticker&market=spot&page=0&limit=50`

Returns Binance USDT-pair 24-hour ticker data, sorted with requested favorites
first and then by descending quote volume.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `market` | string | No | `"spot"` (default) or `"futures"` |
| `page` | number | No | Zero-based page, default 0 |
| `limit` | number | No | Default 50, maximum 100 |
| `query` | string | No | Case-insensitive symbol substring, normalized to uppercase |
| `favorites` | string | No | Comma-separated symbols, e.g. `BTCUSDT,ETHUSDT` |

**Response:**
```json
{
  "items": [
    {
      "symbol": "BTCUSDT",
      "last_price": "67234.50",
      "change_percent_24h": "2.14",
      "quote_volume_24h": "1845234567.00",
      "market_type": "spot",
      "favorite": true
    }
  ],
  "page": 0,
  "count": 1,
  "total": 285,
  "last_page": false
}
```

Binance upstream failures return HTTP 502. No demo prices are substituted.

### Trend Signals

`GET /tradingdata?request_type=trend_signals&page=0&limit=10`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | number | No | Page number (default 0). Page > 0 requires license. |
| `limit` | number | No | Items per page (default 10, max 10) |

**Response:**
```json
{"items": [{"coin_name": "BTC", "graph_type": "240", "timestamp": "1784900000", "signal_type": "LONG", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "status": "active"}], "page": 0, "count": 10, "last_page": false}
```

### Trend Signal Detail

`GET /tradingdata?request_type=trend_signal_detail&coin_name=BTC&graph_type=240&timestamp=1784900000`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `coin_name` | string | Yes | e.g. `"BTC"` |
| `graph_type` | string | Yes | Timeframe in minutes: `"240"` = 4h |
| `timestamp` | string | Yes | Signal timestamp |

**Response:**
```json
{"item": {"coin_name": "BTC", "graph_type": "240", "timestamp": "1784900000", "signal_type": "LONG", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "status": "active", "klines_data": [...]}}
```

Note: `klines_data` only included for licensed users.

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

No auth required. Returns platform config (plans, pricing, banners). Cache locally.

**Response:**
```json
{
  "GENERAL": "general",
  "plans": {"starter": {"monthly_price": 9.99, "monthly_credits": 2}, "pro": {"monthly_price": 29.99, "monthly_credits": 10}},
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

Updated daily by BinancePrecisionLister scheduler. Cache this response — it changes at most once per day.

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

`POST /user?request_type=community_chat_history`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 50, max 100 |
| `before_sort_key` | string | No | Pagination — get messages before this key |

**Response:**
```json
{"ok": true, "data": {"messages": [{"beyin_id": "MTHG7A", "message": "BTC looking bullish!", "created_at": 1784990000, "sort_key": "..."}], "count": 50}}
```

### Create Post (Leaders Only)

`POST /user?request_type=community_post_create`

Only users with `community_role: "leader"` can create posts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Post title |
| `content` | string | Yes | Max 5000 characters |
| `image_url` | string | No | S3 URL for attached image |

**Response:**
```json
{"ok": true, "data": {"post_id": "post_MTHG7A_1784990000"}}
```

Followers are automatically notified via FCM + Telegram.

### List Posts

`POST /user?request_type=community_post_list`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `author_id` | string | No | Filter by leader. Omit for all posts. |
| `limit` | number | No | Default 20, max 50 |

**Response:**
```json
{"ok": true, "data": {"posts": [{"post_id": "...", "author_id": "MTHG7A", "title": "BTC Analysis", "content": "...", "image_url": "", "like_count": 12, "comment_count": 3, "created_at": 1784990000}], "count": 5}}
```

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

3 reports → content is automatically hidden.

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

`POST /user?request_type=community_leaders_list`

No body params.

**Response:**
```json
{"ok": true, "data": {"leaders": [{"beyin_id": "MTHG7A", "name": "CryptoTrader", "bio": "Full-time crypto analyst"}], "count": 3}}
```

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
