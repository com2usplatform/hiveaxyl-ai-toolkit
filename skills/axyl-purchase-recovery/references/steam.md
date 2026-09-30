# Steam microtransactions

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
