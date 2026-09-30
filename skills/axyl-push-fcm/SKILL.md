---
name: axyl-push-fcm
description: "Implements Hive Axyl Android FCM push in Unity: Firebase/permission preparation, token renewal, language/consent changes, and app-policy-driven account binding. Use for Android push integration; does not send campaigns or cover Apple APNs."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Android FCM permission through Axyl registration

Registers an Android device's FCM token with Axyl, and changes an existing
registration's language, consent or player binding. The Installed SDK, SDK results,
Push registration, Push settings and account binding and Android FCM sections below
apply to every step.

**Inputs:** the player's session, the Firebase configuration, country, IANA time
zone, language and the three consents; for a change, the registered device token.
**App owns:** the permission UI, lifecycle, consent storage and the account-binding
policy.

Flow: validate the inputs → `POST_NOTIFICATIONS` on API 33+ → `GetTokenAsync` →
`UpsertTokenAsync` with `Fcm` and the full `Agreement`. A settings or account change
on a known registration skips all of that. Reception and cold start apply only when
requested.

## Verify

- [ ] Both API-level branches work; a denial, or a dialog completing after
  cancellation, makes no token or registration call.
- [ ] Missing Firebase configuration or an empty token stops before registration.
- [ ] A refresh during registration ends with the latest token and full consent, and
  `DeleteTokenAsync` is never a retry.
- [ ] Android delivery and campaign tests are reported separately from source review
  and test doubles.

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

<!-- axyl-shared: core/push-preparation.md -->

## Push registration

Resolve `Hive.Axyl.Push.IPushService`, registered once with `AddPush()`, which
already binds `https://app-api.hiveaxyl.com` (`AddPush(baseUrl)` is only for an
explicitly provisioned host; Push has no sandbox or zone), and the selected APNs or
FCM addon. Registration needs the player's authenticated session, from which the
server takes the player ID. The registration belongs to the device token, so logout
does not remove it. Never log device tokens or notification payloads.

**Registration inputs:** ISO country, an IANA time zone ID, a defined `LanguageCode`
(never `Unspecified`, never parsed from a number), the optional server ID and app
version, and three explicit consents: information, advertising and night
advertising, where `Night = true` requires `Advertise = true`. OS permission is not
consent.

1. Validate the inputs before asking for permission.
2. Check or request permission with the platform procedure. Denial is an expected
   state: stop before the token and the registration.
3. Get a nonempty token and its `UpsertTokenRequestProviderType`: `Apns` or
   `ApnsSandbox` from the actual APNs entitlement environment, `Fcm` for FCM. An
   unknown environment or an empty token stops here.
4. `push.UpsertTokenAsync(new UpsertTokenRequest { Token = deviceToken,
   ProviderType = providerType, Language = language, Country = country,
   TimezoneId = timezoneId, Agreement = new Agreement { Info = infoConsent,
   Advertise = advertiseConsent, Night = nightConsent }, ServerId = serverId,
   AppVersion = appVersion }, new ApiCallContext { Token = ct })`.
5. `PushUpsertTokenResult.Success` means the registry accepted the update
   asynchronously; keep the token and provider type used. It does not prove delivery.

Check cancellation after the permission, token and registration steps; a request
that may have reached the server stays uncertain rather than undone. A settings
change on a known registration uses the settings patches below, never a new
permission prompt or token.

### Token renewal

Subscribe to the plugin's `TokenRefreshed` for the app-owned lifetime and
unsubscribe on teardown. Re-register the latest token with the current account,
environment, language and full consent. Serialize as the recipe does: while a
registration runs, keep only the latest event token, and after `Success` register
again only if it differs. Stop on failure or cancellation; a bounded retry is the
app's choice and must keep the latest desired state. A repeated token, including one
the token lookup itself emits, must not loop permission or token calls.
Registration has no revision field, so client ordering does not prove the server's
write order after a timeout.

<!-- /axyl-shared -->

<!-- axyl-shared: core/push-management.md -->

## Push settings and account binding

Use `Hive.Axyl.Push.IPushService` with the account's authenticated session and the
device token actually registered; a login access token is not a device token. The
recipes do not compose these calls: the coordination below is the app's design.

| Change | Call with `new ApiCallContext { Token = ct }` |
|---|---|
| Language | `PatchTokenLanguageAsync(new PatchTokenLanguageRequest { Token = deviceToken, Language = language }, ctx)` |
| Consent | `PatchTokenAgreementAsync(new PatchTokenAgreementRequest { Token = deviceToken, Agreement = new Agreement { Info = info, Advertise = advertise, Night = night } }, ctx)` |
| Player binding | `DetachTokenIdentifierAsync(new DetachTokenIdentifierRequest { Token = deviceToken }, ctx)` |

Each result has `Success`, `ResourceNotInScope`, `InvalidSubject`, unknown and
`Failure` variants. `Success` means the server accepted the change asynchronously,
not that it was applied or that delivery changed. Keep the latest desired state
after a failure; a typed refusal is no reason to resend it unchanged.

- `Language` is a defined `LanguageCode`, never `Unspecified`.
- The consent patch replaces the whole `Agreement`; `Night = true` requires
  `Advertise = true`. Consent comes from app policy, never from OS permission.
- A new registration or token uses the full `UpsertTokenAsync`; a patch changes one
  setting of a known registration. Run patches and upserts through one app-owned
  update flow that carries account, token and the latest full state, so an old
  result never marks a newer token synchronized. Client ordering does not prove
  server apply order after a timeout.

### Logout and account switch

Whether logout detaches the player binding, and whether a detach failure blocks
logout, is app policy: reuse it or ask the app developer, never add it silently.

| Policy | Boundary |
|---|---|
| Detach on logout | Capture the player and device token, pause queued upserts, and dispatch the detach while that account is still authenticated, before Auth logout; then apply the app's failure policy and the logout result |
| Keep the binding | The token keeps targeting that player; login alone does not rebind it, and an app rebind upserts with the new account and its consent |

Detach removes only the player ID from the registration: it does not delete the
token, revoke OS permission, reset consent or recall queued notifications. Never
send one account's cleanup as another, or retry it with an invalidated token. If the
detach succeeds but Auth logout is refused or cancelled, report that split state;
never rebind automatically or call it a rollback.

<!-- /axyl-shared -->

<!-- axyl-shared: push/fcm.md -->

## Android FCM

Register `AddFCM()` and resolve `Hive.Axyl.Push.Addon.FCM.IFCMPlugin` on Android,
with the app's Firebase configuration (`Assets/Plugins/Android/google-services.json`);
never invent credentials or project IDs.

1. Android API 33+: check `UnityEngine.Android.Permission.HasUserAuthorizedPermission`
   for `android.permission.POST_NOTIFICATIONS` and, if needed, call
   `Permission.RequestUserPermission` with `PermissionCallbacks` and wait for the
   grant or denial. This step is the app's; `IFCMPlugin` has no permission call.
   Lower API levels have no runtime ask, which is not advertising consent.
2. Denial stops before the token. After cancellation, a dialog that completes later
   must not continue the flow. An Editor branch reporting "granted" is a test path only.
3. `fcm.GetTokenAsync(ct)` must return `FcmServiceGetTokenResult.Success` with a
   nonempty `Data.Token`; register it with `UpsertTokenRequestProviderType.Fcm`.
4. Re-register on `TokenRefreshed` under the token renewal rules. `DeleteTokenAsync`
   is neither preparation, logout cleanup nor a retry for a failed registration.

Only when requested: `NotificationReceived` handles reception (a notification
Android shows in the background may not raise it), and cold start uses
`GetColdStartMessageAsync` with the installed launch-intent integration.

<!-- /axyl-shared -->
