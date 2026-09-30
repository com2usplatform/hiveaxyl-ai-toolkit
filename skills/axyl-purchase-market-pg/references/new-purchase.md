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
