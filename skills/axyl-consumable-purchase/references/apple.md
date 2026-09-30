# Apple StoreKit

Register `AddStoreKit()` and resolve
`Hive.Axyl.Payments.Addon.Apple.IAppleStoreKitPlugin` on iOS or macOS (package
`com.com2usplatform.hiveaxyl.payments.addon.apple`). Product IDs and App Store
configuration belong to the app.

## Catalog

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

## Purchase

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

## Unfinished and delayed transactions

Recovery uses `GetUnfinishedTransactionsAsync` and keeps each JWS, ID and objection;
`GetCurrentEntitlementsAsync` is not a substitute. To handle delayed transactions,
subscribe to `TransactionUpdated` before `StartTransactionObserverAsync(new
StartTransactionObserverRequest(), ct)`, deduplicate against pending work and the
ledger, and stop with the app's observer lifetime. Events never record, reach the game
server or finish by themselves.
