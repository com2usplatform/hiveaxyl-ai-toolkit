---
name: axyl-purchase-market-pg
description: "Implements Hive Axyl hosted PG consumable checkout, browser resume and purchase recovery in Unity. Use for payment URLs, OrderRequestOs and quantity inputs, restored-order correlation, game-server verification and delivery, and finalize, including ambiguous same-product orders and WebGL page opening. No PG client addon is required."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# PG hosted payment through delivery and close

Hosted PG consumable checkout, browser resume and recovery, with no PG client
addon. The Installed SDK, SDK results, Payment state and PG hosted payment sections
below apply to every step.

**Inputs:** the catalog product, the player's session, country, language, a
quantity of 1–999, the account UUID and the build's `OrderRequestOs`.
**App owns:** the browser UI, resume timing, pending-state storage and the delivery
ledger.

Read only the requested goal:

| Goal | Read | Completion |
|---|---|---|
| New consumable | [New purchase](references/new-purchase.md) | Pre-purchase → payment URL → external payment and resume → restored, correlated order → record → game-server confirmation (new) → finalize |
| Unfinished consumable | [Recovery](references/recovery.md) | Server restore → no second record → game-server confirmation (recovery) → finalize |

PG subscriptions have no composition here.

## Verify

- [ ] A payment URL, a browser return or a WebGL page opening is never treated as
  payment.
- [ ] Two open orders for one product stay separate until a real correlation.
- [ ] A resumed new purchase records and goes to the game server as new; recovery
  skips the record and goes as a recovery; the client calls no verify API.
- [ ] A finalize failure keeps the delivered order for cleanup, with no new checkout
  or grant.

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

<!-- axyl-shared: payments/pg.md -->

## PG hosted payment

PG uses `IPaymentsService` and a browser the app opens; there is no PG addon.

1. Catalog: `payments.FetchPgProductsAsync(new ProductPg { ProviderId =
   ProductPgProviderId.Pg, Country, Currency, Language, ProductType = "consumable",
   ServerId, AppVersion }, ctx)`; pick the product from
   `PaymentsFetchPgProductsResult.Success` (`ServerId` is not a product filter). An
   empty catalog or a wrong product stops checkout.
2. Validate the quantity (1–999) first, then call `CreatePrePurchaseAsync` with
   `PrePurchaseProviderId.Pg`.
3. `CreatePaymentUrlAsync(new OrderRequest { ProviderId = OrderRequestProviderId.Pg,
   ProductId, Quantity, Os, Country, Language, ServerId, IapPayload, AppVersion },
   ctx)` with `Os` = the build's `OrderRequestOs` member: `Windows`, `Macos`,
   `Android`, `Ios` or `Webgl`. Never send the default `Unspecified`, which the
   server does not accept; a platform without a member cannot offer PG.
4. Open `PaymentsCreatePaymentUrlResult.Success.Data.PayUrl` in the app's browser
   and keep an awaiting-payment state. Neither this nor the pre-purchase gives a
   receipt or order ID. On WebGL, open the page inside the user's click and report
   a blocked popup; never alter the URL.
5. On an explicit resume, `RestorePurchasesAsync(new PurchaseRestoreRequest {
   ProviderId = PurchaseRestoreRequestProviderId.Pg, Country, Language, ServerId,
   AppVersion }, ctx)` returns the real orders in `Restores`. A browser return, a
   dismissed page or an empty list proves nothing.
6. Correlate the restored entry with this purchase through server or order evidence.
   The recipe takes the first matching product, which leaves two open orders for one
   product ambiguous: keep both and require a selection contract, never an invented
   order ID.
7. A resumed new purchase still records: call `RecordStorePurchaseAsync` with the
   restored `AxylReceipt`, `OrderId` and `StoreTransactionId`, then go to the game
   server as a new purchase. Only independent recovery skips the record and goes as
   a recovery.
8. After the game server's delivery confirmation, finalize on the server with its
   closing receipt, or the original sealed receipt. There is no device finish or
   consume.

Never regenerate the page on each resume or loop checkout; resume timing and any
bounded polling are the app's choice.

<!-- /axyl-shared -->
