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

Resolution verified on 2026-07-29:

1. `BeyinFinanceUserAPI` version `2` adds `marketplace_browse` to the public
   Trading Data allow-list and routes it to the active-listings `status-index`.
2. `GET /tradingdata?request_type=marketplace_browse&coin=SPYB` now returns
   HTTP 200 with `{ "listings": [], "count": 0, "has_more": false }`.
3. Publish at least one active listing to validate the non-empty catalog path.

The mobile UI now passes the coin filter correctly and presents explicit
loading, unavailable, and empty states instead of an indefinite skeleton.

## Backtest & strategy engine expansion — pending deployment

Recorded 2026-09-21. The main repo added new backtest and strategy-generation
capabilities in `AWS/BeyinFinanceBacktestOrchestrator.py`,
`AWS/BeyinFinanceBacktestWorker.py`, and `AWS/BeyinFinanceStrategyGenerator.py`,
and declared them in `contracts/strategy_backtest_v1.json`. As of this note the
deployed Lambdas still predate the change (Orchestrator `LastModified`
2026-09-19), so these are **NOT live** and are intentionally **absent from the
public developer reference** (`endpoints.md`) per the not-yet-live rule.

Add to `endpoints.md` ONLY AFTER the carrying Lambda versions are deployed and
verified:

1. Backtest actions (read-only, post-process a completed `job_id`; not subject
   to `backtest_concurrency_limit`, no credit charge):
   - `POST /backtest?action=walk_forward` — field `wf_windows` (int 2..20,
     default 4). Returns per-window return/drawdown/win-rate + a
     robust/mixed/fragile verdict.
   - `POST /backtest?action=monte_carlo` — field `mc_runs` (int 100..5000,
     default 1000). Returns return/drawdown percentiles + probability_of_profit.
2. Portfolio / `resimulate_divide` sizing fields: `position_mode`
   (`compound` default | `fixed` | `risk_pct`), `fixed_amount` (when fixed),
   `risk_pct` (when risk_pct). Also surfaced in the portfolio result.
   NOTE: the same change moves the portfolio `initial_balance` DEFAULT from 100
   to 1000 — update the documented default when it ships.
3. DONE (documented in endpoints.md Create Strategy + Backtest): `strategy_generate`
   fields `exit_type` (`fixed`|`trailing`|`time`|`indicator`|`scaling`, default
   fixed), `trail_pct`, `time_exit_candles`, `exit_condition` (required for
   indicator exit), `entry_type` (`single`|`dca`, default single),
   `dca_steps`, `dca_step_pct`, and `direction_agnostic`
   (default true). Required condition fields now depend on `exit_type`
   (fixed/scaling → tp+sl; trailing/time → sl; indicator → exit_condition+sl).
   Market type, leverage and side are NOT strategy-creation fields — a
   strategy is direction-agnostic and these are chosen on the backtest launch
   actions (`market_type`, `leverage`, `position_side`). Strategy creation and
   edit only take the trading logic; they never accept a market or side.

Sibling surfaces to update in the SAME release (tracked so nothing drifts):
- Public website `Developers.tsx` backtest sample list (add walk_forward,
  monte_carlo; re-check the group `count`).
- Website marketing/blog "three backtest modes" copy (now understated: trailing
  / time / indicator / scaling exits, single / DCA entries, risk-% sizing,
  walk-forward + Monte Carlo robustness).
