# New consumable purchase

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

## Close after delivery

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

## Recover undelivered consumables

Buys nothing new: discover each open transaction at its source, hand it to the game
server as a recovery, and close it once the server confirms delivery. Requires country, language,
the originating account UUID and the optional server ID and app version.

| Market | Discovery |
|---|---|
| Apple | `IAppleStoreKitPlugin.GetUnfinishedTransactionsAsync(new GetUnfinishedTransactionsRequest(), ct)`; keep each transaction's product, original JWS, ID and verification objection. Current entitlements are not a substitute |
| Google | After `StartConnectionAsync(ct)` (`Success` or `AlreadyConnected`), `QueryPurchasesAsync(ProductType.Inapp, ct)` must return `Success`; keep only `PurchaseState.Purchased` entries with products and map each like a fresh purchase (envelope, `PurchaseToken`, `StoreTransactionId = OrderId`). A failed query is not an empty result |
| Steam, PG | `RestorePurchasesAsync(new PurchaseRestoreRequest { ProviderId, Country, Language, ServerId, AppVersion }, ctx)`; keep each `Data.Restores` entry's `AxylReceipt`, `OrderId`, `StoreTransactionId`, product, price, currency and payload, and confirm its market. An empty success does not prove an in-flight payment was cancelled |

1. Build pending state per transaction. Apple and Google entries carry no price or
   currency: take the original values from the app's order ledger or backend, and
   the catalog only for missing data, never zero placeholders.
2. Apple and Google record again: `RecordStorePurchaseAsync(new PurchaseRequest {
   AxylReceipt = recordReceipt, ... })` with the new-purchase fields. Continue on
   `Success` or `PaymentsRecordStorePurchaseResult.VerifyError` only; the game
   server's verification still decides. Steam/PG entries are already recorded: never
   record them again, and only check the restored data locally (a receipt is present,
   the market matches).
3. Send each pending purchase to the game server as a **recovery** (the server
   verifies with request type 2; Google's verification token is the `PurchaseToken`
   with `ProductId`) and wait for its delivery confirmation. The server grants only
   what its ledger lacks.
4. Run the market's new-purchase close with that confirmation.

Track progress per entry: a cancellation or failure keeps the other receipts, and a
partial batch is not "all recovered". A close failure after delivery retries the
close only. Never match two purchases by product ID alone; the PG payment page
response carries no order ID. The recipe names a Google entry by its first product,
so a multi-product purchase needs one entry per product.
