---
name: axyl-subscription
description: "Composes shared Apple/Google subscription startup in Hive Axyl Unity: pre-record, acquisition, save, game-server verification and entitlement, and confirmation. Use for multi-market or unspecified-market subscription flows and common receipt/post invariants; does not implement server renewal jobs."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Start and confirm a subscription

Starts an Apple or Google subscription: pre-record, checkout, save, game-server
verification and entitlement, confirmation and store finish. The Installed SDK, SDK results, Payment
state and Start and confirm a subscription sections below apply to every step.

**Inputs:** the market, the subscription product, the originating player's session,
country, language and the account UUID namespace.
**App owns:** checkout UI, pending-state storage, and the game server's
verification, entitlement ledger, confirmation and renewal processing.

For one named market, prefer `axyl-purchase-market-apple` or
`axyl-purchase-market-google`. Otherwise read only that market's procedure:

| Market | Read | Market steps |
|---|---|---|
| Apple | [Apple StoreKit](references/apple.md) | AutoRenewable catalog, StoreKit purchase, JWS and ID, finish after post |
| Google | [Google Play Billing](references/google.md) | Subscription offers and phases, per-launch `Subs` query and offer token, envelope, device acknowledgement after post |

## Verify

- [ ] Pre → store → save → game-server confirmation → post → finish or acknowledge,
  with one original receipt for save, server verification and post; the client
  calls no verify API.
- [ ] A save conflict or a duplicate post is not a new grant, a missing confirmation
  posts nothing, and a post without `HiveAxylTransactionId` finishes nothing.
- [ ] Google acknowledges on the device (`AlreadyAcknowledged` counts) and never
  consumes; a failed acknowledgement stays pending and recoverable after restart.
- [ ] Google is acknowledged by Axyl's server at post and again on the device; the
  receipt-form gap and the app-exit recovery contract are reported, not assumed.

<!-- axyl-shared: core/installed-sdk.md -->

## Installed SDK

- Read `Packages/manifest.json`, the lock file and each resolved `package.json`.
  All `com.com2usplatform.hiveaxyl.*` packages must be the same release (UPM does
  not enforce this); `com.hive.axyl.*` packages are a release before 1.0.0-rc.9.
- The installed SDK wins for APIs, types and contracts. If its release differs
  from this skill's `sdk-version`, apply a step only after its fields, result
  variants, platform support and failure behaviour match; otherwise stop at that
  step and report what is missing. Never change the installed version.
- The app owns UI, storage, the device key and orchestration. Sample and recipe
  classes are not SDK APIs.

<!-- /axyl-shared -->

<!-- axyl-shared: core/results.md -->

## SDK results

Match each call's concrete result and read `Success.Data` only after checking the
fields the next step needs. The markers live in `Hive.Axyl.Contracts.Result`.

| Result | Handling |
|---|---|
| `IUserCanceledOutcome` | The user dismissed OS or provider UI: stop this attempt quietly |
| `IUnknownOutcome` | Keep `Code` and `RawJson`; never treat it as a known refusal or a success |
| `IUntypedProblem` | Technical failure in `Problem` (`HiveError`): network, timeout or caller `Cancelled` |
| Other typed variant | Only that call's documented meaning |

Pass `new ApiCallContext { Token = ct }` and check cancellation before each
follow-up call; a request cancelled in flight may still have taken effect. Never
branch on HTTP status, exception text or raw bodies, and never log tokens or
credentials.

<!-- /axyl-shared -->

<!-- axyl-shared: core/payment-state.md -->

## Payment state

Resolve `Hive.Axyl.Payments.IPaymentsService`, registered once at startup with
`AddPayments()` (`https://commerce-api.hiveaxyl.com`), `AddPayments(sandbox: true)`
(`https://sandbox-commerce-api.hiveaxyl.com`) or `AddPayments(baseUrl)` for a
provisioned host, as the app's environment selects. Require the originating
player's authenticated session and the selected market's addon; never initialize
per purchase. Never log receipts.

### Retained state

`PurchaseOrder`, `PendingPurchase`, `PurchaseDeliveryConfirmation` and the recipe
sources are sample types: carry the same values in app-owned types through every
stage.

| State | Values |
|---|---|
| Order | Market, originating player, product ID, decimal price, currency, country, language, server ID, app version, IAP payload, account UUID; Steam store player ID |
| Pending | Record receipt, verification token, finish token, order ID, store transaction ID, the order, any local store verification objection |
| Confirmed | The game server's delivery confirmation for that pending purchase, with any updated closing receipt or verified subscription product ID |

A missing addon or input, or a pending purchase from another market, stops before
the next mutation. Keep receipts and IDs after a failure or cancellation: payment
or delivery may already have happened. Persist recoverable state under the app's
storage policy, and coordinate purchase, recovery and account changes so that no
transaction is delivered twice at once or moved to another player.

`AccountUuid` is optional on `PrePurchase`, `PurchaseRequest` and
`SubscriptionPrePurchaseRequest`; an unset one is left off, so the server cannot
compare the account. Set it: derive it as UUIDv5 from the game's fixed namespace UUID
(from game configuration, the same on every platform) and the invariant decimal
player ID string, in standard network byte order (mind C# `Guid`'s layout). Send the
same value as Apple `AppAccountToken`, Google `ObfuscatedAccountId` and in Axyl
requests; the SDK does not generate it.

### Catalog

Apple/Google: use configured product IDs, or call
`ListStoreProductIdsAsync(new StoreRequest { ProviderId, Country, Language,
AppVersion }, ctx)` and select the intended entry of
`PaymentsListStoreProductIdsResult.Success.Data.Stores`: `Products` for consumables,
`ProductSubscriptions` for subscriptions (the request has no product type). An
absent or empty list calls for configured IDs or a catalog diagnosis; never reuse
consumable IDs as subscriptions or invent one. Then query the native store and send
the mapped details with the market's `Fetch*ProductsAsync`. Steam and PG fetch their
server catalog directly.

Each fetch returns its own result over `ProductResponseData`. Choose the
`Data.Products` entry by `ProductId` and `ProductType`, and keep its decimal `Price`,
`Currency` and offers with the response's country and language as the purchase
inputs. Never parse `DisplayPrice`, rescale a decimal into micros or turn a missing
price into zero (a configured zero-price phase is real). A catalog failure, an empty
catalog and a failed checkout are different results. Recovery keeps the original
transaction's price and uses the catalog only for missing data.

### Receipt identities

| Market | Record receipt | Verification token for the game server | Store finish |
|---|---|---|---|
| Apple | Original transaction `JwsRepresentation` | Same JWS | `AppleTransaction.Id` as decimal `ulong` |
| Google | JSON envelope `{"purchase_data": OriginalJson, "signature": Signature}` | Consumable: `PurchaseToken` with `ProductId`; subscription: the envelope | Same `PurchaseToken` |
| Steam | Server `AxylReceipt` from init or restore | Same sealed value | None on the device |
| PG | Server `AxylReceipt` from restore | Same sealed value | None on the device |

Build the Google envelope with a JSON serializer around the untouched
`OriginalJson` string; never parse and reserialize it. A payment URL is never a
receipt. Keep the order ID and store transaction ID as separate values: a restore
entry's `StoreTransactionId` can differ from its order key.

Provider enums are request-specific (`PrePurchaseProviderId`,
`PurchaseRequestProviderId`, `PurchaseFinalizeRequestProviderId`, ...): use the named
`Apple`, `Google`, `Steam` or `Pg` member where it exists; never cast between enums
or default an unknown market.

### Game-server verification, delivery, close

Receipt verification is server to server: the Payments contract marks
`/payment/v1/purchase/verify` and `/payment/v1/subscription/verify` server-only, so
the client SDK has no verify call. After the purchase is recorded, send the pending
purchase to the game's own authenticated server: market, record receipt,
verification token, order ID, store transaction ID, order metadata and account, and
whether it is a new purchase or a recovery (the server maps that to verify request
type 1 or 2).

The game server verifies with the payment backend, checks account, product and price
(for a subscription also current refund and expiry eligibility) and grants once
through its durable ledger. It answers with a delivery confirmation for that pending
purchase, also when the same transaction was already granted, carrying any updated
closing receipt (for a subscription, the verified product ID). The endpoint, request
and response are the app's design. The confirmation is an integration contract, not
proof of payment: the client never manufactures one, and a rejection, failure,
timeout or missing confirmation keeps the pending purchase and closes nothing.

Close only with a confirmation that matches the pending purchase, using the market's
procedure; `RequestPurchaseAsync` and `FinalizePurchaseAsync` run after delivery. A
close failure leaves a delivered, unfinished transaction: retry the close with the
same confirmation, never grant again. Remove the pending record only after the close
succeeds.

`ItemResultAsync(ItemResultBody, ctx)` reports actual delivery (`AxylTransactionId`
from the game server's verification; `Status` 1 success, 2 cancelled without
clawback, 3 cancelled with clawback; `Assets` granted). The recipes do not use it. If
the integration requires it, agree its owner with the backend and report the ledger
result, never status 1 merely because a purchase was recorded.

<!-- /axyl-shared -->

<!-- axyl-shared: payments/subscription.md -->

## Start and confirm a subscription

Apple or Google only: Steam/PG subscriptions have no composition here, so never
route them through Apple or infer a flow from an enum member. Before enabling
Google checkout, agree the acknowledgement recovery below.

1. With the catalog product, price, currency, country, language and account UUID,
   call `PrepareSubscriptionAsync(new SubscriptionPrePurchaseRequest { ProviderId,
   ProductId, Price, Currency, Country, Language, ServerId, IapPayload, AccountUuid,
   AppVersion }, ctx)` **before checkout**. It ties later renewal notifications to
   the player and grants nothing.
2. Acquire a purchased store transaction with the market; keep the original
   receipt, product, account, transaction ID and finish token. Pending, dismissal
   and cancellation stop here.
3. `PurchaseSubscriptionAsync(new SubscriptionPurchaseRequest { ProviderId,
   AxylReceipt = originalReceipt, StoreTransactionId, Price, Currency, Country,
   Language, ServerId, AppVersion }, ctx)`: continue on `Success` or this call's
   `PaymentResourceConflict` (a repeated save); anything else stops.
4. Send the pending subscription to the game server and wait for its delivery
   confirmation; the client calls no verify API. The server verifies the receipt,
   checks current refund and expiry eligibility and grants the entitlement once; a
   refund or an earlier grant alone never earns a fresh entitlement. Renewals are
   the server's job.
5. With that confirmation, `PostSubscriptionAsync(new SubscriptionPurchasePostRequest {
   ProviderId, AxylReceipt = originalReceipt, ProductId = confirmedProductIdOrOriginal,
   Currency, Country, Language, ServerId, AppVersion }, ctx)`, where the product ID is
   the confirmation's verified one when present. **Save, server verification and post
   use the same original receipt**; another receipt can return `Success` without a
   matching subscription.
6. `PaymentsPostSubscriptionResult.Success` needs a nonempty
   `Data.HiveAxylTransactionId` before anything is confirmed or finished; this
   call's `VerifyDuplicated` is the already-confirmed branch and permits the
   remaining store cleanup.
7. Apple: `FinishTransactionAsync` with the original transaction ID. Google:
   `AcknowledgePurchaseAsync(originalPurchaseToken, ct)`, where `AlreadyAcknowledged`
   is success and any other result keeps the subscription pending. Never consume a
   subscription.

Use the named `Apple`/`Google` member of `SubscriptionPrePurchaseRequestProviderId`,
`SubscriptionPurchaseRequestProviderId` and `SubscriptionPurchasePostRequestProviderId`. Keep pending state on every
failure, including a post without a confirmed ID and a failed finish or
acknowledgement; a repeated save or confirmation is not a new grant.

Google save, server verification and post keep the JSON envelope. The SDK's
token-form receipt needs a product ID that the save request lacks: never invent the field
or rewrite the receipt without server confirmation. Google checkout queries the
product as `ProductType.Subs` and takes the offer token from that answer.

### Google acknowledgement responsibility

As the recipe does, Play is told twice: Axyl's server acknowledges the purchase
through the Play Developer API when `/subscription/post` confirms it, and the device
then calls `AcknowledgePurchaseAsync` after post `Success` or `VerifyDuplicated`.
Both are idempotent (`AlreadyAcknowledged` counts as success) and the server guide
asks for both, so one side's failure does not go unnoticed; never skip the device
call. A post `Success` without `HiveAxylTransactionId` confirmed nothing, so that
purchase is still unacknowledged.

Google refunds and revokes a new auto-renewing purchase that is not acknowledged
within three days of PURCHASED (not PENDING); renewals need no new acknowledgement,
and prepaid plans or top-ups under one week allow half the plan duration. See
Google's [processing guide](https://developer.android.com/google/play/billing/integrate#subscriptions)
and [subscription lifecycle](https://developer.android.com/google/play/billing/lifecycle/subscriptions).

Nothing acknowledges the purchase before post succeeds. Persist the receipt,
account, entitlement status, post status and acknowledgement result separately. A
failed save, confirmation, post or device acknowledgement stays urgent recoverable
work even after the entitlement is granted; retry the unfinished step under the
agreed idempotency policy without granting again. The recipes compose no
subscription discovery after restart, so agree a server-owned or other recovery
that still works if the app does not reopen before the deadline.

<!-- /axyl-shared -->
