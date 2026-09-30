---
name: axyl-consumable-purchase
description: "Composes a new Hive Axyl consumable purchase in Unity across the selected market: checkout, record, game-server verification and delivery, and close. Use for the shared purchase lifecycle or multi-market orchestration; interrupted purchases use recovery and recurring products use subscription."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# New consumable purchase

Buys one consumable through the selected market: checkout, record, game-server
verification and delivery, and close. The Installed SDK, SDK results, Payment state and New
consumable purchase sections below apply to every step.

**Inputs:** the configured market and product, the originating player's session,
country, language, the account UUID namespace, the market's prerequisites and the
game server's verification endpoint.
**App owns:** checkout UI, pending-state storage and the game server's verification,
delivery ledger and confirmation.

For one named market, prefer its installed `axyl-purchase-market-*` skill.
Otherwise read only the configured market's procedure before the catalog step:

| Market | Read | Market steps |
|---|---|---|
| Apple | [Apple StoreKit](references/apple.md) | Native catalog, StoreKit purchase, JWS and ID, post then finish |
| Google | [Google Play Billing](references/google.md) | Catalog mapping, per-launch query and offer, purchase event, envelope and token, post then consume |
| Steam | [Steam microtransactions](references/steam.md) | Server catalog, approval listener, init instead of pre-purchase, charge at the game server's verification, finalize |
| PG | [PG hosted payment](references/pg.md) | Server catalog, payment URL, restore and order correlation, finalize |

Interrupted purchases belong to `axyl-purchase-recovery`, recurring products to
`axyl-subscription`.

## Verify

- [ ] Pre-purchase (Steam: init) → acquisition → record → game server (new purchase)
  → its delivery confirmation → market close, with the record receipt,
  verification token and finish identity kept distinct; the client calls no verify
  API.
- [ ] Pending approval, a dismissed or cancelled checkout, a record refusal, or a
  missing or rejected confirmation never reaches close, and the pending purchase is
  kept.
- [ ] A close failure after delivery keeps the transaction and retries only the
  close; a failed or unknown Google post never consumes.
- [ ] Prices stay decimal and come from the selected catalog product; no product,
  price or offer is invented.
- [ ] Source review, test doubles and store or server runs are reported separately.

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

<!-- axyl-shared: payments/consumable.md -->

## New consumable purchase

Use only the selected market's acquisition and close. Inputs: the catalog product
with its price and currency, country, language, the account UUID and the market's
prerequisites.

1. Apple, Google, PG: `CreatePrePurchaseAsync(new PrePurchase { ProviderId,
   ProductId, Price, Currency, Country, Language, ServerId,
   RequestDate = DateTimeOffset.UtcNow, IapPayload, AccountUuid }, ctx)`; require
   success. Steam starts with its init instead.
2. Acquire with the market. Apple and Google must return a purchased transaction,
   not approval-pending or an opened sheet; Steam must be approved; PG returns a URL
   and waits for external payment, and after an explicit resume its receipt comes
   from server restore.
3. Keep the pending state from the receipt identities table.
4. `RecordStorePurchaseAsync(new PurchaseRequest { AxylReceipt = recordReceipt,
   ProviderId, ProductId, Country, Language, Currency, Price, OrderId,
   StoreTransactionId, ServerId, IapPayload, AccountUuid }, ctx)`. A refusal, an
   unknown result or a failure stops before the game server.
5. Send the pending purchase to the game server as a **new purchase** and wait for
   its delivery confirmation; the client calls no verify API.
6. Close with that confirmation.

Check cancellation between stages and keep any receipt already obtained. Never
repeat checkout because a record, the game server or a close failed.

### Close after delivery

| Market | Close |
|---|---|
| Apple | `RequestPurchaseAsync(new PurchasePostRequest { ProviderId = PurchasePostRequestProviderId.Apple, AxylReceipt = originalJws, StoreTransactionId = originalTransactionId }, ctx)`; only `Success` or this call's `VerifyDuplicated` permits `FinishTransactionAsync(new FinishTransactionRequest { TransactionId = parsedUlongId }, ct)` |
| Google | `RequestPurchaseAsync(new PurchasePostRequest { ProviderId = PurchasePostRequestProviderId.Google, AxylReceipt = recordedEnvelope, ProductId = productId, StoreTransactionId = playOrderId }, ctx)`; only `Success` or this call's `VerifyDuplicated` permits `ConsumeAsync(originalPurchaseToken, ct)`. Never consume after a failed or unknown post; after a confirmed post, consume `PurchaseNotFound` means already closed |
| Steam, PG | `FinalizePurchaseAsync(new PurchaseFinalizeRequest { ProviderId, AxylReceipt }, ctx)` with the confirmation's closing receipt when it has one, else the original server receipt; require success |

Apple posts the original JWS and finishes the original ID; Google posts the recorded
envelope and consumes the original token. The confirmation's closing receipt is only
for the server-side finalize. Completion is confirmed delivery plus a successful close; while
the close is pending, keep that state and every recovery input. A subscription
closes differently.

<!-- /axyl-shared -->
