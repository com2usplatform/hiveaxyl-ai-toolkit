---
name: axyl-purchase-market-steam
description: "Implements Hive Axyl Steam microtransaction consumables and recovery in Unity. Use for Steam catalog/init, authorization callbacks, the game-server verification that charges, delivery and finalize. Steam authentication tickets and subscription flows are outside this skill."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Steam purchases through delivery and close

Steam microtransaction consumables and their recovery on Windows and macOS. The
Installed SDK, SDK results, Payment state and Steam microtransactions sections below
apply to every step.

**Inputs:** the provisioned catalog, the player's session with its Steam association
and real Steam player ID, country, language and the account UUID.
**App owns:** Steamworks initialization and callback pumping, checkout UI,
pending-state storage and the delivery ledger.

Read only the requested goal:

| Goal | Read | Completion |
|---|---|---|
| New consumable | [New purchase](references/new-purchase.md) | Catalog → approval listener → init → approval → record → game-server verification (charge) and confirmation → finalize |
| Unfinished consumable | [Recovery](references/recovery.md) | Server restore → no second record → game-server confirmation (recovery) → finalize |

Init replaces the pre-purchase, and neither its receipt nor an approval authorizes a
grant. Steam subscriptions have no composition here.

## Verify

- [ ] The listener starts before init; early, unrelated or denied approvals never
  lead to record.
- [ ] The same order and sealed receipt survive record, the game server's
  verification and finalize; the client calls no verify API.
- [ ] A charge or finalize failure keeps the order; recovery never records or grants
  twice.
- [ ] Steamworks and server runs are reported separately from test doubles.

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

<!-- axyl-shared: payments/steam.md -->

## Steam microtransactions

Requires a signed-in player with the intended Steam association and the real Steam
store player ID. For approval callbacks, register `AddSteamMicrotransactions()` and
resolve `Hive.Axyl.Payments.Addon.Steam.ISteamMicrotransactionsPlugin` on Windows or
macOS; the app initializes Steamworks and pumps its callbacks. This is not the Auth
Steam ticket plugin.

1. Catalog: `FetchSteamProductsAsync(new ProductSteam { ProviderId =
   ProductSteamProviderId.Steam, StorePlayerId, Language, ServerId, AppVersion },
   ctx)`, where the server checks the Steam account; pick the product from
   `PaymentsFetchSteamProductsResult.Success.Data.Products`. Country and currency
   come from that answer, since the request has no such fields.
2. Subscribe to `MicroTxnAuthorizationResponse` and call
   `StartCallbackListenerAsync(ct)` **before** init so an early approval is kept;
   correlate it once init names the order.
3. `InitiatePurchaseAsync(new PurchaseInitRequest { ProviderId =
   PurchaseInitRequestProviderId.Steam, ProductId, Country, Currency, Language,
   StorePlayerId, ServerId, AppVersion, IapPayload }, ctx)` replaces the
   pre-purchase. Require `Success.Data` with a nonempty `AxylReceipt` and keep
   `OrderId` and `StoreTransactionId`; this receipt precedes approval and proves no
   charge.
4. Wait for approval of this app and order. A denial, another order's callback or a
   cancellation stops before record; keep the order when the remote state is unclear.
5. Record (the server confirms approval with QueryTxn), then hand the purchase to the
   game server: its server-to-server verification makes the **actual charge**
   (FinalizeTxn) before it delivers and confirms.
6. After delivery, `FinalizePurchaseAsync` closes the server order without charging
   again. There is no device finish.

Recovery uses server `RestorePurchasesAsync`, whose entries are already recorded.
Stop the listener with its owner's lifetime.

<!-- /axyl-shared -->
