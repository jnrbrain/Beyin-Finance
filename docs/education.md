# Beyin Finance Education API Reference

The Education Marketplace lets **instructors** publish and sell courses,
publications, and bundles, and lets **students** buy, learn, track progress,
and earn verifiable certificates.

**Base URL:** `https://api.beyinfinance.com`

All education routes are versioned under `/education/v1` and are relative to the
base URL, for example:

```
GET https://api.beyinfinance.com/education/v1/catalog
```

This reference covers the surface relevant to **students**, **instructors**
(the Leader Studio), and **developers** integrating with them. Internal
moderation, review-queue, and back-office operations are out of scope and are
not part of the public API.

---

## Authentication

Education endpoints use the same authenticated session as the rest of the
Beyin Finance API, presented as a Bearer token:

```
Authorization: Bearer <session_token>
Content-Type: application/json
```

Public catalog reads accept an optional token: they work unauthenticated, and
when a token is present the response is enriched with viewer-specific state
(such as whether you already own a product). Public certificate verification
requires no token at all.

Every non-public operation is authorized against a **scope** carried by the
session. If your session lacks the scope for an operation the API returns
HTTP 403.

| Scope | Grants |
|-------|--------|
| `education:purchase` | Create checkout sessions |
| `education:orders:read` | Read orders and refund requests |
| `education:orders:write` | Create refund requests |
| `education:learn` | Learning surface: dashboard, library, progress, playback, questions |
| `education:reviews:write` | Create, update, or delete your own reviews |
| `education:certificates:read` | List your certificates |
| `education:certificates:write` | Request certificate issuance |
| `education:studio` | Instructor studio: products, curriculum, submissions, bundles, answers |
| `education:studio:upload` | Instructor media uploads |
| `education:studio:analytics` | Instructor sales analytics and payout statements |

A missing or invalid token returns HTTP 401; see [Errors](#errors).

---

## Conventions

These conventions apply to every education endpoint.

### Money

All monetary values are an integer **`amount_minor`** plus an ISO 4217
**`currency`**. For example `{"amount_minor": 4990, "currency": "USD"}` is
`$49.90`. Never send or parse a decimal amount — always use minor units.

### Pagination

List endpoints are cursor-paginated:

| Query parameter | Type | Description |
|-----------------|------|-------------|
| `cursor` | string | Opaque cursor returned by the previous page. Omit for the first page. |
| `limit` | integer | Page size. |

Send the returned cursor back unchanged to fetch the next page. A null cursor
means the final page. Malformed cursors return HTTP 400 instead of silently
restarting at page one.

### Idempotency

Every state-changing request (`POST`, `PUT`, `PATCH`, and destructive
`DELETE`) requires an **`Idempotency-Key`** header:

```
Idempotency-Key: 3f9a1c7e-2b8d-4a6f-9c1e-77b0a2d4e5f6
```

Generate the key once per logical operation and reuse it for every retry.
Replaying the same key returns the original result rather than performing the
operation twice.

### Optimistic concurrency (ETag / If-Match)

Editable resources (studio products, draft curricula, bundles, enrollment
revision adoption) return an `ETag`. To update one, send the last ETag you
received in an **`If-Match`** header. If the resource changed in the meantime
the API returns HTTP 412 (Precondition Failed) so you never overwrite a newer
version blindly.

---

## Student Flow

A typical student journey and the endpoints for each step:

1. **Discover** — Browse the [catalog](#list-catalog), open a
   [product](#get-product-detail), preview its
   [curriculum](#get-curriculum-preview) and read
   [reviews](#list-product-reviews).
2. **Buy** — Create a [checkout session](#create-checkout-session), then poll
   the [order](#get-order-status) until it is paid.
3. **Learn** — Find purchases in your [library](#list-my-library), open the
   [dashboard](#get-my-dashboard), [resume](#get-resume-target) where you left
   off, and stream lessons through a
   [playback session](#create-playback-session).
4. **Track** — Progress is server-authoritative via
   [playback events](#append-playback-events) and
   [reading progress](#update-reading-progress).
5. **Engage** — [Ask questions](#create-a-question) and leave a
   [review](#create-or-update-my-review).
6. **Finish** — Request a [certificate](#request-certificate-issuance); anyone
   can [verify](#verify-a-certificate) it publicly.
7. **Change of mind** — Request a [refund](#create-a-refund-request) within the
   15-day policy window.

---

## Public Endpoints

No token required (an optional token enriches the response). Rate limited.

### List Catalog

`GET /education/v1/catalog`

Paginated catalog with filters.

| Query parameter | Type | Description |
|-----------------|------|-------------|
| `q` | string | Free-text search (max 120 chars) |
| `topic_ids` | string[] | Up to 5 topic IDs (repeat the parameter) |
| `language` | string | Filter by language |
| `level` | string | `beginner`, `intermediate`, or `expert` |
| `product_type` | string | `course`, `publication`, or `bundle` |
| `price_max` | integer | Maximum price in minor units |
| `price_currency` | string | `TRY`, `USD`, or `EUR` |
| `sort` | string | `relevance` (default), `newest`, `rating`, `price_asc`, `price_desc`, `popularity` |
| `cursor`, `limit` | | See [Pagination](#pagination) |

**Errors:** 400 invalid filter, 429 rate limited.

### Get Product Detail

`GET /education/v1/products/{product_id}`

Full product detail including rating, student count, and — when a token is
supplied — viewer state such as ownership.

**Errors:** 404 not found, 429 rate limited.

### Get Curriculum Preview

`GET /education/v1/products/{product_id}/curriculum`

Locked/preview lesson tree for a published product. Preview lessons are
playable; the rest are marked locked until purchase.

**Errors:** 404 not found, 429 rate limited.

### Search Topics

`GET /education/v1/topics`

Topic taxonomy search.

| Query parameter | Type | Description |
|-----------------|------|-------------|
| `q` | string | Search query, min 2 and max 120 chars |
| `cursor`, `limit` | | See [Pagination](#pagination) |

**Errors:** 400 query too short, 429 rate limited.

### List a Leader's Products

`GET /education/v1/leaders/{leader_id}/products`

Published products for a specific instructor (community leader). Cursor
paginated.

**Errors:** 404 leader not found, 429 rate limited.

### List Product Reviews

`GET /education/v1/products/{product_id}/reviews`

Paginated reviews for a product.

**Errors:** 404 not found, 429 rate limited.

### Verify a Certificate

`GET /education/v1/certificates/verify/{verification_token}`

Public certificate verification — **no authentication required**. Returns
whether the token is valid and the certificate's public details (course,
holder, issue date).

**Errors:** 404 unknown token, 429 rate limited.

### Get Commerce Capabilities

`GET /education/v1/commerce/capabilities`

Storefront commerce capabilities and feature flags — for example whether
checkout is currently open. Clients should read this before showing purchase
UI.

**Errors:** 429 rate limited.

---

## Student Endpoints

Require a session with the scope listed on each endpoint.

### Create Checkout Session

`POST /education/v1/checkouts` — scope `education:purchase`

Initiates a purchase. Requires an `Idempotency-Key` header. Returns a checkout
session the client uses to complete payment.

**Errors:** 400 validation, 401 unauthorized, 409 conflict (duplicate),
422 unprocessable (e.g. checkout closed / not purchasable), 429 rate limited.

### Get Order Status

`GET /education/v1/orders/{order_id}` — scope `education:orders:read`

Owner-scoped order detail. Poll this after checkout to observe payment
progress and entitlement grant.

**Errors:** 401, 403 not owner, 404 not found, 429.

### Get My Dashboard

`GET /education/v1/me/dashboard` — scope `education:learn`

Learning summary with in-progress and completed counts. Served
`Cache-Control: private, no-store`.

**Errors:** 401, 429.

### List My Library

`GET /education/v1/me/library` — scope `education:learn`

Deduplicated entitlement products with per-product status. Cursor paginated,
`private, no-store`.

**Errors:** 401, 429.

### Get Resume Target

`GET /education/v1/me/enrollments/{product_id}/resume` — scope `education:learn`

Last server-authoritative lesson/checkpoint so the client can resume exactly
where the student stopped.

**Errors:** 401, 403 no entitlement, 404 not found, 429.

### Get Enrollment Progress

`GET /education/v1/me/enrollments/{product_id}/progress` — scope `education:learn`

Detailed progress for one enrolled product.

**Errors:** 401, 403, 404, 429.

### Adopt Curriculum Revision

`POST /education/v1/me/enrollments/{product_id}/revision-adoptions` — scope `education:learn`

Opt in to complete a newer curriculum revision. Requires `Idempotency-Key` and
`If-Match` (see [Optimistic concurrency](#optimistic-concurrency-etag--if-match)).
Returns updated enrollment progress.

**Errors:** 401, 403, 409 conflict, 412 precondition failed, 429.

### Create Playback Session

`POST /education/v1/products/{product_id}/playback-sessions` — scope `education:learn`

Starts a secure video playback session after an entitlement check. Requires
`Idempotency-Key`. Returns the session and playback credentials.

**Errors:** 401, 403 no entitlement, 409, 429. Returns `201 Created`.

### Append Playback Events

`POST /education/v1/playback-sessions/{session_id}/events` — scope `education:learn`

Sequential heartbeat / seek / pause / rate event batches. Progress is derived
server-side from these events (with anti-cheat validation), not from
client-reported percentages. Requires `Idempotency-Key`.

**Errors:** 400, 401, 403, 409 out-of-order/duplicate, 429.

### Close Playback Session

`DELETE /education/v1/playback-sessions/{session_id}` — scope `education:learn`

Idempotent session close that persists the last checkpoint. Requires
`Idempotency-Key`.

**Errors:** 401, 403, 429.

### Update Reading Progress

`PUT /education/v1/me/enrollments/{product_id}/reading-progress` — scope `education:learn`

Versioned checkpoint for PDF/article reading progress. Requires
`Idempotency-Key`. Returns updated enrollment progress.

**Errors:** 401, 403, 429.

### Create or Update My Review

`PUT /education/v1/products/{product_id}/reviews/me` — scope `education:reviews:write`

Upsert your own review (rating + comment) for a product. Requires
`Idempotency-Key`.

**Errors:** 400, 401, 403 (e.g. no entitlement), 429.

### Delete My Review

`DELETE /education/v1/products/{product_id}/reviews/me` — scope `education:reviews:write`

Delete your own review. Requires `Idempotency-Key`. Returns a deletion receipt.

**Errors:** 401, 403, 404, 429.

### Create a Question

`POST /education/v1/products/{product_id}/questions` — scope `education:learn`

Ask a question on a product you are entitled to. Requires `Idempotency-Key`.
Returns `201 Created`.

**Errors:** 400, 401, 403 no entitlement, 429.

### Resolve a Question

`PATCH /education/v1/questions/{question_id}` — scope `education:learn`

Mark your question resolved or update its state. Requires `Idempotency-Key`.

**Errors:** 401, 403, 404, 409, 429.

### Create a Refund Request

`POST /education/v1/orders/{order_id}/refund-requests` — scope `education:orders:write`

Initiate a refund within the **15-day** policy window. Requires
`Idempotency-Key`. Returns `201 Created`.

**Errors:** 400, 401, 403, 409 (already requested), 422 (outside window /
not refundable), 429.

### Get a Refund Request

`GET /education/v1/orders/{order_id}/refund-requests/{refund_request_id}` — scope `education:orders:read`

Owner-scoped refund request status.

**Errors:** 401, 403, 404, 429.

### Request Certificate Issuance

`POST /education/v1/me/certificates` — scope `education:certificates:write`

Request certificate generation after completing a course. Requires
`Idempotency-Key`. Returns `201 Created` with the certificate (including its
public verification token).

**Errors:** 400, 401, 403 (not completed), 409 (already issued), 429.

### List My Certificates

`GET /education/v1/me/certificates` — scope `education:certificates:read`

Paginated list of your certificates.

**Errors:** 401, 429.

---

## Instructor Endpoints (Leader Studio)

For approved community **leaders** publishing and managing paid content.
Require scope `education:studio` unless a more specific scope is noted. All
state changes require an `Idempotency-Key`; metadata edits also require
`If-Match`.

### Instructor Flow

1. **Onboard** — Check [seller status](#get-seller-status) gates, then
   [start onboarding](#start-seller-onboarding) (contract, tax, e-document,
   bank, identity).
2. **Author** — [Create a product](#create-a-product) draft and
   [edit its metadata](#update-a-product); [replace the draft
   curriculum](#replace-draft-curriculum).
3. **Upload media** — [Create an upload](#create-an-upload), fetch
   [part URLs](#get-presigned-part-urls), upload parts to S3, report
   [part receipts](#report-part-completions), then
   [complete](#complete-an-upload) it. [Reconcile](#reconcile-upload-parts),
   [retry](#retry-upload-processing), or [abort](#abort-an-upload) as needed.
4. **Publish** — [Submit for review](#submit-a-product-for-review); later
   [unpublish](#unpublish-a-product) to stop new sales.
5. **Bundle** — [Create](#create-a-bundle) and [update](#update-a-bundle)
   bundles of your own products.
6. **Support & earn** — [Answer questions](#answer-a-question), read
   [sales analytics](#get-sales-analytics), and review
   [payout statements](#list-payout-statements).

### Get Seller Status

`GET /education/v1/seller/status`

Vendor readiness gates: contract, tax, e-document, AP bank, and identity.

**Errors:** 401, 403, 429.

### Start Seller Onboarding

`POST /education/v1/seller/onboarding-sessions`

Initiate an onboarding session for a community leader. Requires
`Idempotency-Key`. Returns `201 Created`.

**Errors:** 401, 403, 409, 429.

### Create a Product

`POST /education/v1/studio/products`

Create a new course or publication draft. Requires `Idempotency-Key`. Returns
`201 Created`.

**Errors:** 400, 401, 403, 409, 429.

### Update a Product

`PATCH /education/v1/studio/products/{product_id}`

Metadata update. Requires `Idempotency-Key` and `If-Match`.

**Errors:** 400, 401, 403, 409, 412, 429.

### Replace Draft Curriculum

`PUT /education/v1/studio/products/{product_id}/curriculum`

Full replacement of the draft curriculum tree. Requires `Idempotency-Key` and
`If-Match`.

**Errors:** 400, 401, 403, 409, 412, 429.

### Create an Upload

`POST /education/v1/studio/uploads` — scope `education:studio:upload`

Register a multipart upload; returns the part policy and lease. Requires
`Idempotency-Key`. Returns `201 Created`.

**Errors:** 400, 401, 403, 409, 429.

### List Uploads

`GET /education/v1/studio/uploads` — scope `education:studio:upload`

Your transfers, cursor paginated.

| Query parameter | Type | Description |
|-----------------|------|-------------|
| `status` | string | `pending`, `uploading`, `processing`, `completed`, `failed`, `aborted` |
| `cursor`, `limit` | | See [Pagination](#pagination) |

**Errors:** 401, 403, 429.

### Get Presigned Part URLs

`POST /education/v1/studio/uploads/{upload_id}/part-urls` — scope `education:studio:upload`

Batch presigned URLs for **missing parts only** (max 16 per call). Requires
`Idempotency-Key`.

**Errors:** 400, 401, 403, 404, 409, 429.

### Report Part Completions

`POST /education/v1/studio/uploads/{upload_id}/part-receipts` — scope `education:studio:upload`

Idempotent part-completion reporting. Requires `Idempotency-Key`. Returns the
updated upload status.

**Errors:** 400, 401, 403, 404, 409, 429.

### Get Upload Status

`GET /education/v1/studio/uploads/{upload_id}` — scope `education:studio:upload`

Server snapshot of upload status (authoritative, not client-reported bytes).

**Errors:** 401, 403, 404, 429.

### Abort an Upload

`DELETE /education/v1/studio/uploads/{upload_id}` — scope `education:studio:upload`

Idempotent cancellation. Requires `Idempotency-Key`.

**Errors:** 401, 403, 404, 429.

### Reconcile Upload Parts

`POST /education/v1/studio/uploads/{upload_id}/reconcile` — scope `education:studio:upload`

Reconcile against S3 `ListParts` after a client/process loss. Requires
`Idempotency-Key`.

**Errors:** 401, 403, 404, 409, 429.

### Complete an Upload

`POST /education/v1/studio/uploads/{upload_id}/complete` — scope `education:studio:upload`

Validate checksum/manifest and trigger processing. Requires `Idempotency-Key`.

**Errors:** 400, 401, 403, 404, 409, 422, 429.

### Retry Upload Processing

`POST /education/v1/studio/uploads/{upload_id}/processing-retries` — scope `education:studio:upload`

Retry processing for retryable errors only. Requires `Idempotency-Key`.

**Errors:** 401, 403, 404, 409, 422, 429.

### Submit a Product for Review

`POST /education/v1/studio/products/{product_id}/submissions`

Create an immutable review snapshot for moderation. Requires `Idempotency-Key`.
Returns `201 Created` with a submission receipt.

**Errors:** 400, 401, 403, 409, 422, 429.

### Unpublish a Product

`POST /education/v1/studio/products/{product_id}/unpublish`

Close new sales while preserving existing student entitlements. Requires
`Idempotency-Key`.

**Errors:** 401, 403, 404, 409, 429.

### Create a Bundle

`POST /education/v1/studio/bundles`

Create a bundle of your own products (single-leader vendor only). Requires
`Idempotency-Key`. Returns `201 Created`.

**Errors:** 400, 401, 403, 409, 429.

### Update a Bundle

`PATCH /education/v1/studio/bundles/{bundle_id}`

Update bundle metadata. Requires `Idempotency-Key` and `If-Match`.

**Errors:** 400, 401, 403, 409, 412, 429.

### Answer a Question

`POST /education/v1/studio/questions/{question_id}/answers`

Answer a student question on your product. Requires `Idempotency-Key`.

**Errors:** 400, 401, 403, 404, 409, 429.

### Get Sales Analytics

`GET /education/v1/studio/analytics/sales` — scope `education:studio:analytics`

Sales summary with an optional paginated breakdown.

| Query parameter | Type | Description |
|-----------------|------|-------------|
| `period` | string | `day`, `week`, `month` (default), or `all_time` |
| `cursor`, `limit` | | See [Pagination](#pagination) |

**Errors:** 401, 403, 429.

### List Payout Statements

`GET /education/v1/studio/payout-statements` — scope `education:studio:analytics`

Vendor accounts-payable statements with gross / deductions / net. Cursor
paginated.

**Errors:** 401, 403, 429.

---

## Errors

All errors return a JSON body with a descriptive message:

```json
{"error": "Descriptive error message"}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid session token |
| 403 | Authenticated but not allowed (missing scope, not owner, no entitlement) |
| 404 | Not found |
| 409 | Conflict (duplicate, or state does not allow the operation) |
| 412 | Precondition failed — stale `If-Match` ETag |
| 422 | Unprocessable — request is well-formed but violates a business rule (e.g. checkout closed, refund outside window) |
| 429 | Rate limited — retry after backoff |

Retry `429` with exponential backoff and jitter. On `412`, re-read the resource
to obtain the current ETag before retrying. On `409` for an idempotent
operation, treat the stored result as authoritative rather than resubmitting.
