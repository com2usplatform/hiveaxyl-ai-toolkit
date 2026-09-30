# Google Play Billing

Register `AddPlayBilling()` and resolve
`Hive.Axyl.Payments.Addon.Google.IGooglePlayBillingPlugin` on Android, with the Play
configuration and the selected catalog product. Connect first:
`StartConnectionAsync(ct)` continues on `Success` or `AlreadyConnected`.

## Catalog

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

## Purchase

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

## Close

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
