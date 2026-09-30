---
name: axyl-purchase-market-apple
description: "Implements Hive Axyl Apple StoreKit payments in Unity on iOS/macOS. Use when Apple consumable checkout, unfinished-purchase recovery or subscription startup is requested, including JWS handoffs and original-transaction finish. Apple sign-in uses the authentication skill."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Apple payments through market completion

Apple StoreKit consumables, their recovery and subscription startup on iOS and
macOS. The Installed SDK, SDK results, Payment state and Apple StoreKit sections
below apply to every step.

**Inputs:** configured products, the originating player's session, country,
language and the account UUID namespace.
**App owns:** checkout UI, pending-state storage and the delivery or entitlement
ledger.

Read only the requested goal:

| Goal | Read | Completion |
|---|---|---|
| New consumable | [New purchase](references/new-purchase.md) | Pre → purchased transaction → record → game-server confirmation → Apple post → finish |
| Unfinished consumable | [Recovery](references/recovery.md) | Unfinished transactions → record again → game-server confirmation (recovery) → remaining post and finish |
| Subscription | [Subscription](references/subscription.md) | Subscription pre → store → save → game-server confirmation → subscription post → finish |

Keep the original JWS, transaction ID and account association apart from the game
server's confirmation. The recovery record exception and each post's duplicate
branch apply only to their own calls.

## Verify

- [ ] The JWS reaches record, the game server and post; the original `Id` reaches
  finish, and the client calls no verify API.
- [ ] `Pending` and `UserCanceled` grant nothing; an unverified transaction keeps its
  JWS for the game server's verification.
- [ ] A failed finish after delivery retries only the finish, and a subscription
  post without a confirmed transaction ID finishes nothing.
- [ ] StoreKit configuration and device runs are reported separately from test doubles.

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

<!-- axyl-shared: payments/apple.md -->

## Apple StoreKit

Register `AddStoreKit()` and resolve
`Hive.Axyl.Payments.Addon.Apple.IAppleStoreKitPlugin` on iOS or macOS (package
`com.com2usplatform.hiveaxyl.payments.addon.apple`). Product IDs and App Store
configuration belong to the app.

### Catalog

1. Get the product IDs as the catalog rules say, then call
   `storeKit.GetProductsAsync(new GetProductsRequest { ProductIds = ids }, ct)` and
   require `AppleStoreKitServiceGetProductsResult.Success.Data.Products`. A missing
   product needs configuration diagnosis, never a made-up price.
2. Map each selected product to `Hive.Axyl.Payments.ProductAppleProducts`: `Id`,
   `DisplayName`, `Description`, `DisplayPrice`, decimal `Price`, `PriceLocale`
   unchanged and `(int)ProductType` (Apple's raw product code). Keep only the
   requested kind: Consumable, or AutoRenewable for subscriptions.
3. `payments.FetchAppleProductsAsync(new ProductApple { ProviderId =
   ProductAppleProviderId.Apple, Country, Currency, Language, ProductType =
   requestedType, AppVersion, Products = mappedProducts }, ctx)`, where the outer
   `requestedType` is `"consumable"` or `"subscription"`; require
   `PaymentsFetchAppleProductsResult.Success`.

### Purchase

After the pre-purchase (or subscription pre) succeeds, call
`storeKit.PurchaseAsync(new Hive.Axyl.Payments.Addon.Apple.PurchaseRequest {
ProductId = productId, Options = new PurchaseOptions { AppAccountToken =
accountUuid, Quantity = quantity } }, ct)` with a quantity of at least one. This
addon `PurchaseRequest` is not `Hive.Axyl.Payments.PurchaseRequest`.

- `AppleStoreKitServicePurchaseResult.UserCanceled`: stop this attempt.
- `Pending`: approval is not complete; no grant or finish.
- `Success`: require `Data.Transaction` with a nonempty `JwsRepresentation` and its
  original `Id`. Pass any `VerificationStatus`/`VerificationError` objection to the
  game server, and keep the JWS for its verification even then.

The JWS is the record receipt and the game server's verification token; the `Id` (a
decimal `ulong`) is the finish ID and `StoreTransactionId`. Finish only after the
game server's delivery confirmation: a consumable posts then finishes, a subscription posts the subscription
then finishes.

### Unfinished and delayed transactions

Recovery uses `GetUnfinishedTransactionsAsync` and keeps each JWS, ID and objection;
`GetCurrentEntitlementsAsync` is not a substitute. To handle delayed transactions,
subscribe to `TransactionUpdated` before `StartTransactionObserverAsync(new
StartTransactionObserverRequest(), ct)`, deduplicate against pending work and the
ledger, and stop with the app's observer lifetime. Events never record, reach the game
server or finish by themselves.

<!-- /axyl-shared -->
