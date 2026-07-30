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
