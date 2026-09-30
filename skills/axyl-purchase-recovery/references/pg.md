# PG hosted payment

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
