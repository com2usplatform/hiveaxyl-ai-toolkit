---
name: axyl-purchase-market-google
description: "Implements Hive Axyl Google Play Billing in Unity on Android. Use for Google consumables, unconsumed-purchase recovery or subscription startup, including per-launch product/offer queries, purchase callbacks, receipt handoffs, post-then-consume and device acknowledgement. Google sign-in is a separate flow."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Google Play payments through market completion

Google Play consumables, their recovery and subscription startup on Android. The
Installed SDK, SDK results, Payment state and Google Play Billing sections below
apply to every step.

**Inputs:** configured products and offers, the originating player's session,
country, language and the account UUID namespace.
**App owns:** checkout UI, pending-state storage and the delivery or entitlement
ledger.

Read only the requested goal:

| Goal | Read | Completion |
|---|---|---|
| New consumable | [New purchase](references/new-purchase.md) | Pre → purchased event → record → game-server confirmation → post → consume |
| Unfinished consumable | [Recovery](references/recovery.md) | In-app query → record again → game-server confirmation (recovery) → post → consume |
| Subscription | [Subscription](references/subscription.md) | Subscription pre → store → save → game-server confirmation → subscription post → device acknowledgement |

Before enabling subscription checkout, read the
[acknowledgement responsibility](references/subscription.md#google-acknowledgement-responsibility):
Axyl's server acknowledges at post and the device acknowledges again, but nothing
acknowledges before post, so plan deadline-aware recovery that survives app exit.

## Verify

- [ ] Each launch uses a fresh product query and its offer token; the handler is
  subscribed before launch and only a correlated `Purchased` event continues.
- [ ] The envelope goes to record and post, `PurchaseToken` to the game server's
  consumable verification and to consume; subscriptions keep the envelope for save,
  server verification and post; the client calls no verify API.
- [ ] A failed or unknown post never consumes, `PurchaseNotFound` after a confirmed
  post is closed, and subscriptions are acknowledged, never consumed.
- [ ] Already owned leads to recovery; a failed purchase query is not zero purchases.
- [ ] Device and server runs are reported separately; the reviewed sources contain none.

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

<!-- axyl-shared: payments/google.md -->

## Google Play Billing

Register `AddPlayBilling()` and resolve
`Hive.Axyl.Payments.Addon.Google.IGooglePlayBillingPlugin` on Android, with the Play
configuration and the selected catalog product. Connect first:
`StartConnectionAsync(ct)` continues on `Success` or `AlreadyConnected`.

### Catalog

Get the product IDs as the catalog rules say and query them with
`QueryProductDetailsAsync(ids, ProductType.Inapp or ProductType.Subs, ct)`. Native
results are `Hive.Axyl.Payments.Addon.Google.GoogleProductDetails`; server requests
take `Hive.Axyl.Payments.ProductDetails`. Check each product in
`Success.Data.ProductDetailsList` and `UnfetchedProductList`: a partial success does
not mean the selected product was queried.

- Map `ProductId`, `Title`, `Description` and the numeric `(int)ProductType`.
- One-time offers (`OneTimePurchaseOfferDetails` and its list) map to
  `ProductGoogleOfferDetails`: `FormattedPrice`, decimal `PriceAmount`,
  `PriceCurrencyCode`, `OfferId`, `OfferToken`. Keep `PreorderDetails` and
  `RentalDetails` as raw `ToJson()` strings when present; they affect price selection.
- Subscription offers map to `ProductGoogleSubscriptionOffer` (`BasePlanId`,
  `OfferId`, `OfferToken`, `OfferTags`, `PricingPhases`), and each phase to
  `ProductGooglePricingPhase` (`FormattedPrice`, decimal `PriceAmount`,
  `PriceCurrencyCode`, `BillingPeriod`, `BillingCycleCount`, numeric
  `RecurrenceMode`). A trial phase is not the recurring phase.
- The native price is already decimal: never multiply it or fill `PriceAmountMicros`.

Then call `payments.FetchGoogleProductsAsync(new ProductGoogle { ProviderId =
ProductGoogleProviderId.Google, Country, Currency, Language, ProductType =
requestedType, AppVersion, Products = mappedProducts }, ctx)`, where the outer
`requestedType` is `"consumable"` or `"subscription"`, and require
`PaymentsFetchGoogleProductsResult.Success`.

### Purchase

1. After the pre-purchase succeeds, query the product again before **every**
   launch with `QueryProductDetailsAsync(new[] { productId }, type, ct)` and require
   it in `ProductDetailsList`; a launch without it fails with `PRODUCT_NOT_QUERIED`.
   Take the `OfferToken` from this answer: the recipe uses the first subscription
   offer with a token, else the first one-time offer with one, else none. Another
   choice is the game's policy and must match the pre-purchase price.
2. Subscribe to `PurchasesUpdated`, then call `LaunchBillingFlowAsync(new
   LaunchBillingFlowRequest { Products = new[] { new LaunchBillingFlowProductParams {
   ProductId = productId, OfferToken = selectedOfferToken } },
   ObfuscatedAccountId = accountUuid }, ct)`.
3. Launch success only opened the sheet. Wait for an event whose `Purchases` holds
   this product in `PurchaseState.Purchased`, telling purchases apart by token, not
   product. `BillingResult.ResponseCode` 0 means inspect the purchases, 1 user
   cancellation and 7 already owned (recover that purchase, never check out again);
   keep any other code as a technical failure. Pending is not purchased.
4. Keep `OriginalJson`, `Signature`, `PurchaseToken`, `OrderId` and `Products`
   untouched. Record and post send the envelope as `AxylReceipt`; the game server's
   consumable verification uses the `PurchaseToken` with `ProductId`; `OrderId` is
   both the order ID and `StoreTransactionId`.
5. Unsubscribe on every exit. Caller cancellation stops the wait, not a Play
   purchase in progress: keep any later transaction for app-owned reconciliation.

### Close

**Consumable:** after the game server's delivery confirmation, call
`payments.RequestPurchaseAsync(new PurchasePostRequest { ProviderId =
PurchasePostRequestProviderId.Google, AxylReceipt = recordedEnvelope, ProductId =
productId, StoreTransactionId = playOrderId }, ctx)`. Only `Success` or this call's
`VerifyDuplicated` permits `ConsumeAsync(originalPurchaseToken, ct)`; never consume
after a failed or unknown post, because consume removes the purchase from Play's
recovery list. Axyl's server also consumes the purchase through the Play Developer
API at post, so after a confirmed post, consume `PurchaseNotFound` means already
closed. The contract makes `productId` optional with the envelope and documents
`storeTransactionId` for Apple only, but the recipe sends both and says the server
needs the product ID: send both, and treat that server behaviour as unconfirmed.

**Subscription:** after save, the game server's confirmation and post, call
`AcknowledgePurchaseAsync(originalPurchaseToken, ct)`; `AlreadyAcknowledged` is
success and anything else keeps it pending. Never consume a subscription. Axyl's
server has already acknowledged at post; this device call is the recipe's second,
idempotent acknowledgement and always runs.

**Recovery:** connect, then `QueryPurchasesAsync(ProductType.Inapp, ct)`; keep the
`PurchaseState.Purchased` entries with products, map them like a fresh purchase (the
entry has no price or currency), record again, hand it to the game server as a
recovery and close the same way.

The reviewed sources contain no device or live-server run of the Google paths, and
a multi-product purchase is recovered under its first product only.

<!-- /axyl-shared -->
