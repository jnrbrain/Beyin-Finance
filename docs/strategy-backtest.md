# Strategy, backtest, and publishing

Use this flow to create a private strategy, simulate its results, and, if the
result qualifies, publish a Marketplace listing. Generation and backtest
launches spend credits. Publishing makes a listing visible to others.

Use the two headers from [Quickstart](quickstart.md#verify-the-credential).
Paths below are relative to `https://api.beyinfinance.com`.

## 1. Generate a strategy

Send [`POST /user?request_type=strategy_generate`](endpoints.md#create-strategy)
with a unique `Idempotency-Key` header and a strategy body.

```json
{
  "strategy_name": "emaexample",
  "signal_mode": "signal_orders",
  "entry_condition": "Enter when EMA 9 crosses above EMA 21 on a closed candle",
  "tp_condition": "Take profit at 5% from entry",
  "sl_condition": "Stop at a 3% move against the entry"
}
```

Save the strategy name and idempotency key before sending the request. An
accepted generation starts in `generating` and reserves 1 credit. If the
response is interrupted, retry the same request with the same key and body.
If the inputs change, use a new key for the new operation.

Read [strategy detail](endpoints.md#get-strategy-detail) with the same
`strategy_name`. Show the current `phase` while `status` is `generating`. Once
`phase` is `completed`, continue to the estimate. If generation reaches
`failed` or `cancelled`, stop polling and keep the entry visible. Show
`last_error` or `capability_summary` when present. An in-progress generation
can be [cancelled](endpoints.md#cancel-strategy-generation).

## 2. Estimate and launch a backtest

Send [Estimate Cost](endpoints.md#estimate-cost) with your strategy and
instrument. Use `estimated_cost_credits`, `can_afford`, and
`within_runtime_budget` to decide whether to offer launch.

```json
{
  "strategy_name": "emaexample",
  "symbol": "BTCUSDT",
  "timeframe": "4h"
}
```

With these parameters, choose [Full Range Backtest](endpoints.md#full-range-backtest-for-marketplace)
if the result is intended for Marketplace publishing. For a specific date range,
use [Run Specified Range Backtest](endpoints.md#run-specified-range-backtest) for
one instrument or [Launch Portfolio Backtest](endpoints.md#launch-portfolio-backtest)
for several. Follow the parameters for the selected action. The launch reserves
1 credit per eligible instrument. Send a unique `Idempotency-Key` and keep
it with the request inputs. Save the returned `job_id` before starting
status polling.

## 3. Track and recover a job

Send [`POST /backtest?action=status`](endpoints.md#poll-status) with
`{"job_id":"<job_id>"}`. Use a bounded polling interval and back off when the
service asks you to wait.

| Status | What to show and do |
|--------|---------------------|
| `queued`, `running`, `scanning`, `merging` | Keep the job visible. Show `progress_pct` and per-instrument progress when available. |
| `completed` | Stop polling and open [Get Result](endpoints.md#get-result). |
| `failed`, `cancelled` | Stop polling. Keep the history entry and show the reason or refund information when returned. |

If the launch response is lost, retry within 24 hours with the original key
and inputs. If the key is unavailable, check
[Backtest History](endpoints.md#backtest-history) before launching again. Use
[Cancel a Backtest](endpoints.md#cancel-a-backtest) for a job you no longer need.
On HTTP `409` during cancellation, refresh its status to see whether the result
is being saved or is already available.

## 4. Publish a verified result

1. Wait for a completed full-history result for the same strategy. Open
   [Get Result](endpoints.md#get-result) with `result_view: "marketplace"`.
2. Select the instruments and confirm the listing terms. For an original
   result, omit `backtest_saved_revision` or send `0`. For a saved portfolio,
   send the exact `saved_revision` from the result and use its selected coins.
3. Submit [Publish Strategy](endpoints.md#publish-strategy) with the result's
   `job_id` as `backtest_job_id` and a fresh `Idempotency-Key`. The API checks
   result and coin eligibility.
   If the result is stale, reopen it and confirm the selection before resubmitting.

Retain the returned `listing_id`. If the response is interrupted, retry within
24 hours with the same key and inputs or check
[My Listings](endpoints.md#my-listings) for the listing.
