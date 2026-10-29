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

### `marketplace_browse` limit divergence (code vs public docs)

The deployed browse handler `_td_handle_marketplace_browse`
(`AWS/src/user_api/00_prelude/40_public_klines.py`) clamps `limit` internally at
**1000** (`max(1, min(_td_to_int(params.get("limit", 1000), 1000), 1000))`),
while the public reference `endpoints.md` advertises a maximum page size of
**100**. This is a known code/doc divergence: the public contract value (100)
is the one integrators must follow, and the larger internal cap should be
brought down on the code side in a later change. Do not raise the public
documented cap to 1000.

## Backtest & strategy engine expansion — deployed, authenticated verification pending

Recorded 2026-09-21, revalidated against the source contract on 2026-10-29, and
the carrying strategy/backtest Lambda handlers were deployed on 2026-10-29.
The deployment passed package, unit-test, lint and unauthenticated OPTIONS/401
smoke checks, but an authenticated portfolio job was not run in that session
because no valid JWT/test account was available. The capabilities below remain
**out of the public live request tables and examples** until the authenticated
portfolio → result → resimulation/paging → robustness chain is verified.

After that verification, add to `endpoints.md`:

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
   The result also exposes the raw-entry source, deterministic allocation
   policy, entered/skipped counts and financial invariant diagnostics.
   Portfolio signals are paged from the full entered+skipped union store.
3. Strategy generation is only partially expanded in production:
   `direction_agnostic` (default true) is live, and market type, leverage, side
   and timeframe are selected later. The live order-strategy model remains a
   single entry with fixed `tp_condition` + `sl_condition`.

   Strategy create/edit delivery hardening is live in the same API surface:
   clients preserve `Idempotency-Key` across retries; a `generation_id` binds
   the generation task to one atomically charged registry attempt; failure refund and
   in-flight slot release are one transaction. The generation task
   uses Claude Sonnet 4.6 first and falls back to GPT-6.1 Sol through Amazon
   Bedrock only for Anthropic access/availability failures.

   The advanced fields `exit_type` (`fixed`|`trailing`|`time`|`indicator`|
   `scaling`), `trail_pct`, `time_exit_candles`, `exit_condition`, `entry_type`
   (`single`|`dca`), `dca_steps` and `dca_step_pct` have lifecycle status
   **`configuration_pending`**. The User API handler and the machine contract do
   not currently accept them as production behavior. Move them into the live
   developer reference only after handler/generator/client support, contract
   tests, deployment and live verification all advance together.

Sibling surfaces to update in the SAME release (tracked so nothing drifts):
- Public website `Developers.tsx` backtest sample list (add walk_forward,
  monte_carlo; re-check the group `count`).
- Website marketing/blog copy must not advertise advanced exit or DCA behavior
  as available while those fields are `configuration_pending`. Revisit the copy
  only in the same release that makes the contract live.
