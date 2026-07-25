# Beyin Finance Developer API Reference

**Base URL:** `https://08rxd1g3ik.execute-api.eu-central-1.amazonaws.com/BeyinAPI`

---

## Authentication

All requests require API key headers:

```
X-API-Key: bf_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
X-API-Secret: bf_sec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

Generate API keys from the mobile app (Settings → API Keys) or via `api_key_generate`.

---

## Rate Limits

| Plan | Requests/min |
|------|-------------|
| starter | 30 |
| plus | 60 |
| pro | 120 |
| investor | 240 |

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

---

## Economic News & Calendar

### Get Economic Data

`POST /user?request_type=economic_news`

**Cost:** 0.01 ⚡ per request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | No | `"all"` (default), `"news"`, or `"calendar"` |
| `limit` | number | No | Max items per category (default 20, max 50) |

**Example body:**
```json
{"type": "news", "limit": 10}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "news": [
      {"id": "a3b2c1d4e5f6", "type": "news", "title": "Fed issues enforcement action", "source": "fed", "source_url": "https://...", "sentiment": "NEUTRAL", "impact": "MEDIUM", "category": "FED", "affected_coins": ["BTC"], "timestamp": 1784900000}
    ],
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
| `strategy_name` | string | Yes | Unique, lowercase alphanumeric (`^[a-z0-9]+$`) |
| `market_type` | string | Yes | `"spot"` or `"futures"` |
| `signal_mode` | string | Yes | `"signal_orders"` or `"signal_only"` |
| `timeframe` | string | Yes | `1m,3m,5m,15m,30m,1h,2h,4h,1d` |
| `entry_condition` | string | Yes | Entry condition in natural language |
| `tp_condition` | string | Yes* | Take profit (*required for signal_orders) |
| `sl_condition` | string | Yes* | Stop loss (*required for signal_orders) |
| `visibility` | string | No | `"private"` (default) or `"public"` |
| `price_per_signal` | number | No | 0-10, required if visibility=public |

**Cost:** 1.0 ⚡ total (0.05 upfront + 0.95 on success)

**Example body:**
```json
{"strategy_name": "emacross", "market_type": "spot", "signal_mode": "signal_orders", "timeframe": "4h", "entry_condition": "EMA 9 crosses above EMA 21", "tp_condition": "Price reaches +3%", "sl_condition": "Price drops -2%"}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "version": 1, "signal_mode": "signal_orders", "status": "generating", "cost_upfront": 0.05, "cost_on_success": 0.15}}
```

**Errors:** 402 insufficient credits, 409 name taken.

### Edit Strategy

`POST /user?request_type=strategy_edit`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_name` | string | Yes | Existing strategy you own |
| `entry_condition` | string | No | New entry condition |
| `tp_condition` | string | No | New take profit |
| `sl_condition` | string | No | New stop loss |

Bumps version, triggers AI regeneration. **Cancels all marketplace copiers/subscriptions.**

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

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `visibility` | string | Yes | `"private"` or `"public"` |
| `price_per_signal` | number | No | 0-10 for public |

**Example body:**
```json
{"strategy_name": "emacross", "visibility": "public", "price_per_signal": 0.5}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "visibility": "public", "price_per_signal": 0.5}}
```

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

**Example body:**
```json
{"strategy_name": "emacross", "target_version": 2}
```

**Response:**
```json
{"ok": true, "data": {"strategy_name": "emacross", "new_version": 4, "rolled_back_to": 2}}
```

---

## Backtest

**Endpoint:** `POST /backtest?action=<action>`

Backtests run asynchronously with parallel workers. Flow: `run` → `status` (poll) → `result`.

**Cost model:** Total = AWS cost × 5. Deducted as 1/5 upfront + 4/5 on success. Failed jobs are auto-refunded.

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

### Get Data Info

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
{"action": "list_timeframes", "coin": "BTC", "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]}
```

### Run Backtest

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

Each coin runs as a separate chunk. Required for `marketplace_publish` with `signal_mode=full`.

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

### Delete Backtest

`POST /backtest?action=delete_backtest`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | Yes |
| `backtest_key` | string | Yes |

**Response:**
```json
{"action": "delete_backtest", "success": true, "strategy_name": "emacross", "backtest_key": "1784936800_6a2326"}
```

### Backtest History

`POST /user?request_type=backtest_history`

| Field | Type | Required |
|-------|------|----------|
| `strategy_name` | string | No | Filter by strategy |

**Response:**
```json
{"ok": true, "data": {"backtests": [{"job_id": "...", "strategy_name": "emacross", "coin": "BTC", "timeframe": "4h", "cost_credits": 0.05, "summary": {"total_trades": 7, "win_rate": 71.43, "total_return_pct": 5.46}}], "count": 50}}
```

---

## Signals

### Active Signals

`POST /user?request_type=active_signals`

No body params.

**Response:**
```json
{"ok": true, "data": {"signals": [{"position_key": "emacross#BTC#1784850000", "coin": "BTC", "strategy_name": "emacross", "owner": "MTHG7A", "side": "LONG", "signal_mode": "full", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "source": "user", "created_at": 1784850000}], "count": 1}}
```

### Signal History

`POST /user?request_type=signal_history`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filters.coin` | string | No | Filter by coin |
| `filters.strategy_name` | string | No | Filter by strategy |
| `filters.owner` | string | No | Filter by owner |
| `page_size` | number | No | Default 20, max 50 |
| `last_evaluated_key` | string | No | Pagination cursor (base64) |

**Example body:**
```json
{"filters": {"coin": "BTC", "strategy_name": "emacross"}, "page_size": 20}
```

**Response:**
```json
{"ok": true, "data": {"signals": [{"closed_key": "...", "coin": "BTC", "strategy_name": "emacross", "side": "LONG", "signal_mode": "full", "entry_price": "67234.50", "limit_price": "69500.00", "stop_price": "65800.00", "exit_price": "69500.00", "result": "GAIN", "source": "user", "created_at": 1784850000, "closed_at": 1784950000}], "last_evaluated_key": "base64..."}}
```

---

## Automated Trading

All automated trading endpoints return the same structure with `bot_settings`, `limits`, `counts`, `catalog`, and `sync` fields.

### Get Status

`POST /user?request_type=automated_trading_status`

No body params. Returns full bot settings + available coins.

**Response:**
```json
{
  "bot_settings": {"automated_trading_enabled": true, "allocation_pct": 100, "strategy_configs": {"emacross": {"key": "emacross", "name": "emacross", "source": "user", "enabled": true, "coins": ["BTC", "ETH"]}}},
  "limits": {"strategies": 3, "coins": 10},
  "counts": {"total_strategies": 2, "user_strategies": 1, "system_strategies": 1},
  "catalog": [{"key": "emacross", "name": "emacross", "source": "user", "coins": []}],
  "sync": {"bindings_created": 0, "bindings_removed": 0},
  "available_coins": ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX"]
}
```

### Update Settings

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
- 400: `"Max N user strategies allowed for your plan"` — plan limit reached

### Remove Strategy

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
| `filters.market_type` | string | No | `"spot"` or `"futures"` |
| `filters.timeframe` | string | No | e.g. `"4h"` |
| `filters.signal_mode` | string | No | `"full"` or `"signal_only"` |
| `filters.min_win_rate` | number | No | Min win rate % |
| `filters.coins` | string[] | No | Filter by listed coins |
| `page_size` | number | No | Default 20, max 50 |
| `last_evaluated_key` | string | No | Pagination cursor (base64) |

**Example body:**
```json
{"filters": {"market_type": "spot", "min_win_rate": 55, "coins": ["BTC"]}, "page_size": 20}
```

**Response:**
```json
{"ok": true, "data": {"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "owner": "MT***A", "market_type": "spot", "timeframe": "4h", "signal_mode": "full", "listed_coins": ["BTC", "ETH"], "signal_price_credits": 0.5, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "subscriber_count": 5, "total_signals_delivered": 42}], "last_evaluated_key": "base64..."}}
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
    "signal_mode": "full",
    "listed_coins": ["BTC", "ETH"],
    "signal_price_credits": 0.5,
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
{"ok": true, "data": {"subscription_id": "sub_xyz789", "listing_id": "lst_abc123", "strategy_name": "emacross", "active_coins": ["BTC", "ETH"], "signal_price_credits": 0.5, "bindings_created": 2}}
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
{"ok": true, "data": {"listings": [{"listing_id": "lst_abc123", "strategy_name": "emacross", "status": "active", "signal_mode": "full", "market_type": "spot", "timeframe": "4h", "listed_coins": ["BTC"], "signal_price_credits": 0.5, "subscriber_count": 5, "total_signals_delivered": 42, "total_credits_earned": 21.0, "total_pnl_pct": 12.5, "win_rate_pct": 68.0, "created_at": 1784000000}]}}
```

### My Subscriptions

`POST /user?request_type=marketplace_my_subscriptions`

No body params.

**Response:**
```json
{"ok": true, "data": {"subscriptions": [{"subscription_id": "sub_xyz789", "listing_id": "lst_abc123", "creator_beyin_id": "ABC123", "selected_coins": ["BTC"], "status": "active", "signal_price_credits": 0.5, "signals_received": 12, "credits_spent": 6.0, "created_at": 1784000000}]}}
```

### Publish Strategy

`POST /user?request_type=marketplace_publish`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_key` | string | Yes | Lowercase alphanumeric |
| `description` | string | No | Max 500 chars, no HTML |
| `signal_price_credits` | number | Yes | 0.01 - 100.0 |
| `signal_mode` | string | Yes | `"full"` or `"signal_only"` |
| `requested_coins` | string[] | Yes | Coins to list |

**Requirements for `signal_mode=full`:** Must have a successful `full_range` backtest. Only coins with **positive PnL** and **≥10 trades** are listed. Others are rejected.

**Example body:**
```json
{"strategy_key": "emacross", "description": "EMA crossover for BTC", "signal_price_credits": 0.5, "signal_mode": "full", "requested_coins": ["BTC", "ETH", "SOL"]}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "status": "active", "listed_coins": ["BTC", "ETH"], "rejected_coins": {"SOL": "negative_pnl", "DOGE": "insufficient_trades"}, "signal_price_credits": 0.5, "signal_mode": "full", "backtest_summary": {"BTC": {"pnl_pct": 12.5, "win_rate": 68.0, "trades": 42}}}}
```

**Errors:** 400 no full_range backtest found, 400 no profitable coins.

### Update Listing

`POST /user?request_type=marketplace_update_listing`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing_id` | string | Yes | |
| `signal_price_credits` | number | No | 0.01 - 100.0 |
| `description` | string | No | Max 500 chars |

⚠️ **Price change cancels ALL active subscriptions** and removes bindings.

**Example body:**
```json
{"listing_id": "lst_abc123", "signal_price_credits": 1.0, "description": "Updated description"}
```

**Response:**
```json
{"ok": true, "data": {"listing_id": "lst_abc123", "updated_fields": ["signal_price_credits"], "subscriptions_cancelled": 3, "note": "Price changed 0.5 -> 1.0. All subscriptions cancelled."}}
```

### Unpublish Listing

`POST /user?request_type=marketplace_unpublish`

| Field | Type | Required |
|-------|------|----------|
| `listing_id` | string | Yes |

Cancels all subscriptions, removes bindings, sets status to "removed".

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

Must have (or had) a subscription to review. One review per user per listing. Cannot review own listing.

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

### Platform Notifications

`GET /tradingdata?request_type=platform_notifications&limit=20`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Default 20, max 50 |

**Response:**
```json
{"notifications": [{"title": "New Feature", "body": "Marketplace is now live!", "type": "announcement", "timestamp": 1784900000}], "count": 1}
```

---

## General Config

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
