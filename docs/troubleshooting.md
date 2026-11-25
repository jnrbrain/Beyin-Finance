# Troubleshooting

Check the HTTP status and any documented `code`, `reason`, or `reason_code`
fields in the body. Display `error` or `message` to help the user understand the
outcome. Use machine-readable values to decide whether your integration should
retry or ask the user to change something.

For Education, read `error.code`, `error.message`, and `error.retryable` from
the [nested error object](education.md#errors).

## Verify authentication

| Response | Next step |
|----------|-----------|
| `401 invalid_credentials` | Verify both headers and their exact values. Check the credential in account settings. Replace it if it has been revoked or cannot be recovered. |
| `401` with a documented session error | If you are building a session-based client, follow the session rules for that operation. Developer API requests use the key pair. |
| `403` | Check the operation's authentication mode, account access, and ownership requirements. |
| `403 insufficient_api_key_scope` | Read `required_scope`. In account settings, revoke and create a replacement key with the needed permission if authorized. |
| `403 first_party_auth_required` | Use the official app or dashboard for that operation. |
| `503 api_key_store_unavailable` | Retry an eligible request with backoff. Keep the existing credentials. |

See [Authentication](endpoints.md#authentication) for the supported surfaces
and [Education authentication](education.md#authentication) for session-based
Education operations.

## Respect throttling

On HTTP `429`, wait for the `Retry-After` delay when the API provides it.
If it is absent, use capped exponential backoff with jitter for requests that
can be retried safely. Set a retry limit and respect the caller's overall
timeout. [Rate Limit Headers](endpoints.md#rate-limit-headers) describes the
remaining request budget when a route provides it.

For `backtest_concurrency_limit` or `strategy_generation_in_progress`, continue
following the existing work. Use the [strategy and backtest guide](strategy-backtest.md)
to find and cancel work you no longer need.

## Recover from an uncertain outcome

| Situation | Next step |
|-----------|-----------|
| A read times out or gets a temporary service error | Retry with backoff within your time budget. |
| Strategy create or edit loses its response | Reuse the same `Idempotency-Key` and request body as documented for the operation. On `409 idempotency_conflict`, check the original request and use a new key for a new operation. |
| A backtest launch or Marketplace publish loses its response | Retry within 24 hours with the original `Idempotency-Key` and inputs. If no key was sent, check [Backtest History](endpoints.md#backtest-history) or [My Listings](endpoints.md#my-listings) before resubmitting. |
| An Education checkout loses its response | Reuse the same key, product, price version, and storefront for a newly created checkout. If you have the order ID, check [Get Order Status](education.md#get-order-status). |
| A live order's outcome is unknown | Check [Order History](endpoints.md#get-order-history) or Binance before resubmitting. Follow the operation's reconciliation and idempotency rules. |
| A backtest result exceeds the response limit | Use [Get All Trades or Signals](endpoints.md#get-all-trades-or-signals) for available paginated records. See [Get Result](endpoints.md#get-result) for the result-size behavior. |
| Education returns a stale-version error | Fetch the latest resource and review its changes before retrying with its current `ETag`. |

## Contact support

Keep the method, route and operation name, UTC timestamp, HTTP status, error
code, and the `X-Correlation-ID` response header when provided. Include the
strategy or job ID if relevant. Remove credentials, signed URLs, and private
account details from any logs you share. See
[Request correlation](endpoints.md#request-correlation) and the
[Errors reference](endpoints.md#errors).
