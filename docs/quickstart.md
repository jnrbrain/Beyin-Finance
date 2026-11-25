# Quickstart

Make a public market-data request, then verify your Developer API credentials
with a read-only account request. Both examples use the production API.

## Get a public market quote

Copy this request into your terminal. On Windows PowerShell, use `curl.exe`
if `curl` resolves to a PowerShell alias.

```bash
curl --fail-with-body --silent --show-error --max-time 20 'https://api.beyinfinance.com/tradingdata?request_type=market_quote&symbol=BTCUSDT&market=spot'
```

An HTTP `200` response includes `symbol`, `bid_price`, `ask_price`, and
`timestamp`. The price fields are decimal strings and `timestamp` is in
milliseconds since the Unix epoch. The quote changes with the market.
See [Market Quote](endpoints.md#market-quote) for the full response.

## Create Developer API credentials

1. On the [web dashboard](https://beyinfinance.com/dashboard/settings), open
   **Settings → Developer API Key**. In the mobile app, open
   **Account → Settings → Developer API**.
2. Create a credential. Save both values in your server's secret manager.
   The secret is displayed at creation. Use the values exactly as issued.
   Start with the default `read` permission and enable any additional
   [permissions](endpoints.md#authentication) your integration needs.
3. Provide those values to the process running the example as `BF_API_KEY`
   and `BF_API_SECRET`.

```{warning}
Keep the key and secret on a trusted server. Keep them out of frontend bundles,
mobile apps you distribute, URLs, logs, screenshots, and support messages.
Keys with `trade` can place or cancel supported orders on a linked exchange
account. Grant that permission only to an integration you trust with live
orders. Revoke a credential from account settings if it is exposed.
```

## Verify the credential

Send both headers to read your account's own details. This request spends
no credits and places no orders.

```bash
curl --fail-with-body --silent --show-error --max-time 20 \
  'https://api.beyinfinance.com/user?request_type=account_info' \
  -H "X-API-Key: $BF_API_KEY" \
  -H "X-API-Secret: $BF_API_SECRET" \
  -H 'Content-Type: application/json' \
  --data '{}'
```

In PowerShell, use `curl.exe`, replace `$BF_API_KEY` and `$BF_API_SECRET` with
`$env:BF_API_KEY` and `$env:BF_API_SECRET`, and put the command on one line
without the trailing `\` characters.

Look for HTTP `200`, `ok: true`, and `data.plan`. Avoid logging the full
account response. If the request fails, see
[Troubleshooting](troubleshooting.md#verify-authentication).

## Choose your next step

- [Strategy, backtest, and publishing guide](strategy-backtest.md) for credits
  and asynchronous progress.
- [Developer API Reference](endpoints.md) for route-specific authentication,
  input fields, and responses.
- [Education API Reference](education.md) for guest catalog reads and
  session-based student and instructor flows. Check commerce availability
  before integrating checkout.
