# Runtime Integration Notes

This document records verified API/UI integration findings that require a
backend deployment or a contract update. It is not part of the public API
guarantee.

## Trend Break history

Verified on 2026-07-29 with DynamoDB record `SPYB#15 / 1785333096`:

- DynamoDB contains `200` entries in `klines_data`.
- The public `trend_signals` response currently exposes those 200 entries.
- The public `trend_signal_detail` response omits `klines_data` and returns
  only the two `low_trend` anchors.
- The detail response also exposes storage-only fields that must be removed.

Impact: a detail screen that requests `trend_signal_detail` without an
in-memory list snapshot can only draw two anchor points, not a 200-candle
chart.

Required contract alignment:

1. Keep list responses lightweight and free of storage-only fields.
2. Return the full 200-candle snapshot from `trend_signal_detail` for the
   Trend Break history viewer.
3. Preserve exactly two anchor points per trend line and stop the drawn trend
   line at the break candle; post-break candles are context only.

The mobile client now forwards an already-received candle snapshot to the
detail route and falls back to a historical kline request if it is absent.

## Marketplace browse

Verified on 2026-07-29:

- `BeyinFinanceMarketplaceListings` is active but contains zero listings.
- The deployed `BeyinFinanceUserAPI` returns HTTP `405` for
  `request_type=marketplace_browse` even though the repository source contains
  a public browse handler.
- Marketplace listing data is DynamoDB-backed; S3 is not part of the browse
  path.

Impact: the mobile Marketplace Bots section cannot complete its initial read.

Resolution — in source (live confirmation still pending):

1. **In source (verified):** `BeyinFinanceUserAPI` adds `marketplace_browse` to
   the public Trading Data allow-list and provides a browse handler. The
   allow-list entry is in `AWS/src/user_api/00_prelude/30_trading_data.py` (both
   the authenticated and guest sets) and the handler
   `_td_handle_marketplace_browse` is in
   `AWS/src/user_api/00_prelude/40_public_klines.py`;
   `contracts/endpoint_traceability.json` lists `marketplace_browse` as
   `screen_connected` under `trading_data`.
2. **Response shape (from source):**
   `GET /tradingdata?request_type=marketplace_browse&coin=SPYB` is expected to
   return HTTP 200 with `{ "listings": [], "count": 0, "has_more": false }`
   while `BeyinFinanceMarketplaceListings` holds zero active listings. Whether
   the fix is live in the deployed UserAPI is a **runtime fact not confirmable
   from code in this pass**; treat the 405→200 transition as "verified in
   source / pending live confirmation", not a confirmed current live fact.
3. **Still unvalidated:** the non-empty catalog path. The listings table is
   empty, so a browse against real listings has not been exercised. Publish at
   least one active listing to validate it.

The mobile UI now passes the coin filter correctly and presents explicit
loading, unavailable, and empty states instead of an indefinite skeleton.

### `marketplace_browse` page-size contract

The public browse handler `_td_handle_marketplace_browse`
(`AWS/src/user_api/00_prelude/40_public_klines.py`) now uses the documented
default of **50** and caps the page size at **100**. The DynamoDB query and the
public reference therefore enforce the same limit. Do not raise the public
documented cap above 100 without a versioned contract change.

## Backtest & strategy engine contract — source aligned, authenticated verification pending

Recorded 2026-09-21, revalidated against the source contract on 2026-10-29, and
the carrying strategy/backtest Lambda handlers were deployed on 2026-10-29.
The deployment passed package, unit-test, lint and unauthenticated OPTIONS/401
smoke checks, but an authenticated portfolio job was not run in that session
because no valid JWT/test account was available. The source and public reference
now list the available backtest actions, but that deployment evidence does not
prove the complete authenticated portfolio → result → resimulation/paging →
robustness chain works end to end. Treat that user workflow as **runtime
verification pending**, not as an undocumented or unavailable API contract.

The current source-aligned public contract includes:

1. Backtest actions (read-only, post-process a completed `job_id`; not subject
   to `backtest_concurrency_limit`, no credit charge):
   - `POST /backtest?action=walk_forward` — field `wf_windows` (int 2..20,
     default 4). Returns per-window return/drawdown/win-rate + a
     robust/mixed/fragile verdict.
   - `POST /backtest?action=monte_carlo` — field `mc_runs` (int 100..5000,
     default 1000). Returns return/drawdown percentiles + probability_of_profit.
2. Portfolio / `resimulate_divide` sizing fields: `position_mode`
   (`compound` default | `fixed` | `risk_pct`), `fixed_amount` (when fixed),
   `risk_pct` (when risk_pct, 0.1–100). Fixed stakes must be positive and are
   skipped when free balance cannot cover them. Risk sizing targets the given
   percentage of available free balance at the stop and includes the simulator's
   leverage, commission and spread assumptions (with loss capped at the stake).
   Invalid sizing values are rejected with HTTP 400. Also surfaced in the
   portfolio result.
   The portfolio launch action currently defaults `initial_balance` to `100`;
   `resimulate_divide` uses the saved job value unless the caller supplies an
   override. Keep these defaults distinct in the public reference.
   The result also exposes the raw-entry source, deterministic allocation
   policy, entered/skipped counts and financial invariant diagnostics.
   Portfolio signals are paged from the full entered+skipped union store.
3. Strategy generation is only partially expanded in production:
   `direction_agnostic` (default true) is live, and market type, leverage, side
   and timeframe are selected later. The live order-strategy model remains a
   single entry with condition-based `tp_condition` + `sl_condition`. Both live
   and M1-backtest evaluation use one chronological list: `[-1]` is the newest
   forming target bar and `[-2]` the latest closed bar. At an exact target-bar
   boundary, the M1 replayer moves the completed bar to `[-2]` and creates a
   boundary-price stub at `[-1]`, so close-confirmed entries can be evaluated
   at that boundary without lookahead. Intrabar conditions may still use `[-1]`.
   The generator returns concrete per-signal exit prices after evaluating the
   entry and exit conditions. A live lookback above 1,000 candles is marked
   `LIVE_CANDLE_LIMIT` and remains backtest-only. Backtests do not have a fixed
   target-candle ceiling: launch preflight converts the selected lookback to
   1-minute warmup rows, adds each chunk's source rows and maximum-hold lookahead,
   and returns `422 RUNTIME_LIMIT` before charging when the estimated execution
   time exceeds its safe budget. This forecast is approximate; the execution
   timeout remains the final guard.

   Runtime parity details deployed to production on 2026-11-15: Binance
   supplies the live target timeframe, including its forming `[-1]` bar. In S3 mode, the worker
   reads closed 1-minute rows and aggregates the target timeframe's forming
   `[-1]` bar from those rows; the latest completed target bar remains `[-2]`.
   A missing 1-minute interval is reported as a data gap instead of shifting
   indices. Open-position TP/SL tracking uses closed 1-minute bars from the
   persisted per-signal cursor, at most 1,000 rows per invocation. A gap does not
   advance that cursor or close the position. When one 1-minute OHLC candle
   touches both TP and SL, the stop is resolved first; across different minutes,
   the first level touched in time wins. The worker, backtest, generator and API
   Lambda updates all reached `LastUpdateStatus=Successful`; the IAM alert-marker
   permission update reached `UPDATE_COMPLETE`. The unauthenticated preview route
   returned the expected HTTP 401 `session_expired`; no exchange order was sent.

   Unless the caller sets a custom value, backtest `min_gap_candles` now derives
   from the live cooldown: `ceil(max(timeframe seconds,
   MIN_SIGNAL_INTERVAL_SECONDS) / timeframe seconds)`. The live interval is
   currently 3,600 seconds by default; explicit backtest overrides remain
   supported.

   The app signal detail adds a read-only Spot-entry preview and a separate
   confirmation step for a Spot `BUY MARKET` order. The entry does not submit
   TP/SL/OCO exits. App and Telegram share a per-signal atomic claim so one signal
   cannot be entered twice. Futures and short submissions remain blocked. An
   unresolved Binance result is reported as unknown and must be checked in
   Binance order history before retrying. The UserAPI and Telegram backend flows
   are deployed. The mobile entry UI remains source-only until a mobile client
   release; no authenticated order flow was exercised during deployment checks.

   Strategy capability tags include exact/approximate support, ambiguity,
   contradiction, data/lookahead/limit/runtime/exit failures. A safe equivalent
   implementation rewrite is internal. App and web strategy detail screens can
   open a generated suggestion in AI revision mode. Telegram now provides the
   same revision action for saved strategies and a separately confirmed retry
   using a failed generation's stored suggestion. It calls the same UserAPI
   `strategy_edit`/`strategy_generate` logic and uses a short-lived scoped internal
   assertion. The API and Telegram flows are deployed; app/web revision UI changes
   remain source-only until their respective client release.

   Strategy create/edit delivery hardening is live in the same API surface:
   clients preserve `Idempotency-Key` across retries; a `generation_id` binds
   the generation task to one atomically charged registry attempt; failure refund and
   in-flight slot release are one transaction. GPT-6.1 Sol through Amazon
   Bedrock is the active primary provider. Claude is disabled and retained only
   as commented fallback code. Generation prefers one GPT request and retries
   invalid/provider-failed responses up to three total attempts. User prompts
   and generated Python are logged for debugging. Prompts may be written in any
   language; strategy intent must be understood in the original language.

Sibling surfaces already aligned with the source contract:
- Public API reference and website API playground include `result_trades`,
  `resimulate_divide`, `walk_forward`, and `monte_carlo`.
- Website marketing/blog copy must not advertise advanced exit or DCA behavior
  as available while those fields are `configuration_pending`. Revisit the copy
  only in the same release that makes the contract live.

## Backtest saved views — verified 2026-11-18

Production BacktestOrchestrator and UserAPI were deployed on 2026-11-18.
An isolated GPTEST fixture verified conditional save/retry/conflict, reopened
portfolio and independent coin summaries, order pages, strict positive-profit
eligibility and protection against invalidating an existing saved portfolio.
The original result bytes and credit balance remained unchanged. The fixture
was removed after the checks. Marketplace publishing reads the original
`<strategy>_full_range.json` artifact; saving a view does not rewrite it.

Conditional snapshot writes follow the [AWS S3 conditional-write contract](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html).
