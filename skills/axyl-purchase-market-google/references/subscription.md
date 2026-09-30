# Start and confirm a subscription

Apple or Google only: Steam/PG subscriptions have no composition here, so never
route them through Apple or infer a flow from an enum member. Before enabling
Google checkout, agree the acknowledgement recovery below.

1. With the catalog product, price, currency, country, language and account UUID,
   call `PrepareSubscriptionAsync(new SubscriptionPrePurchaseRequest { ProviderId,
   ProductId, Price, Currency, Country, Language, ServerId, IapPayload, AccountUuid,
   AppVersion }, ctx)` **before checkout**. It ties later renewal notifications to
   the player and grants nothing.
2. Acquire a purchased store transaction with the market; keep the original
   receipt, product, account, transaction ID and finish token. Pending, dismissal
   and cancellation stop here.
3. `PurchaseSubscriptionAsync(new SubscriptionPurchaseRequest { ProviderId,
   AxylReceipt = originalReceipt, StoreTransactionId, Price, Currency, Country,
   Language, ServerId, AppVersion }, ctx)`: continue on `Success` or this call's
   `PaymentResourceConflict` (a repeated save); anything else stops.
4. Send the pending subscription to the game server and wait for its delivery
   confirmation; the client calls no verify API. The server verifies the receipt,
   checks current refund and expiry eligibility and grants the entitlement once; a
   refund or an earlier grant alone never earns a fresh entitlement. Renewals are
   the server's job.
5. With that confirmation, `PostSubscriptionAsync(new SubscriptionPurchasePostRequest {
   ProviderId, AxylReceipt = originalReceipt, ProductId = confirmedProductIdOrOriginal,
   Currency, Country, Language, ServerId, AppVersion }, ctx)`, where the product ID is
   the confirmation's verified one when present. **Save, server verification and post
   use the same original receipt**; another receipt can return `Success` without a
   matching subscription.
6. `PaymentsPostSubscriptionResult.Success` needs a nonempty
   `Data.HiveAxylTransactionId` before anything is confirmed or finished; this
   call's `VerifyDuplicated` is the already-confirmed branch and permits the
   remaining store cleanup.
7. Apple: `FinishTransactionAsync` with the original transaction ID. Google:
   `AcknowledgePurchaseAsync(originalPurchaseToken, ct)`, where `AlreadyAcknowledged`
   is success and any other result keeps the subscription pending. Never consume a
   subscription.

Use the named `Apple`/`Google` member of `SubscriptionPrePurchaseRequestProviderId`,
`SubscriptionPurchaseRequestProviderId` and `SubscriptionPurchasePostRequestProviderId`. Keep pending state on every
failure, including a post without a confirmed ID and a failed finish or
acknowledgement; a repeated save or confirmation is not a new grant.

Google save, server verification and post keep the JSON envelope. The SDK's
token-form receipt needs a product ID that the save request lacks: never invent the field
or rewrite the receipt without server confirmation. Google checkout queries the
product as `ProductType.Subs` and takes the offer token from that answer.

## Google acknowledgement responsibility

As the recipe does, Play is told twice: Axyl's server acknowledges the purchase
through the Play Developer API when `/subscription/post` confirms it, and the device
then calls `AcknowledgePurchaseAsync` after post `Success` or `VerifyDuplicated`.
Both are idempotent (`AlreadyAcknowledged` counts as success) and the server guide
asks for both, so one side's failure does not go unnoticed; never skip the device
call. A post `Success` without `HiveAxylTransactionId` confirmed nothing, so that
purchase is still unacknowledged.

Google refunds and revokes a new auto-renewing purchase that is not acknowledged
within three days of PURCHASED (not PENDING); renewals need no new acknowledgement,
and prepaid plans or top-ups under one week allow half the plan duration. See
Google's [processing guide](https://developer.android.com/google/play/billing/integrate#subscriptions)
and [subscription lifecycle](https://developer.android.com/google/play/billing/lifecycle/subscriptions).

Nothing acknowledges the purchase before post succeeds. Persist the receipt,
account, entitlement status, post status and acknowledgement result separately. A
failed save, confirmation, post or device acknowledgement stays urgent recoverable
work even after the entitlement is granted; retry the unfinished step under the
agreed idempotency policy without granting again. The recipes compose no
subscription discovery after restart, so agree a server-owned or other recovery
that still works if the app does not reopen before the deadline.
