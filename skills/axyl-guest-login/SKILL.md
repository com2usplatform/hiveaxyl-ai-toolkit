---
name: axyl-guest-login
description: "Implements first-run or returning guest login in Unity with the Hive Axyl SDK, through token exchange and session installation. Use for guest creation/restoration and retaining guest recovery credentials after failure. Does not implement saved access/refresh-token auto login."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Guest login

Creates a guest on first run or restores the saved one, then installs an Axyl
session. The Installed SDK, SDK results, Axyl session and Login metadata sections
below apply to every step.

**Inputs:** Axyl `clientId`, the device's `deviceKey`, the saved
`(PlayerId, GuestToken)` if any, and an optional app-server grant key.
**App owns:** credential storage, guest UI, error display and result types.

## Flow

1. Create one PKCE pair for the attempt.
2. **No saved credential:** `var created = await auth.CreateGuestAsync(new
   GuestCreateRequest { ClientId, DeviceKey, CodeChallenge, CodeChallengeMethod =
   CodeChallengeMethod.S256, GrantKey }, ctx)`. On `AuthCreateGuestResult.Success`,
   persist `(Data.PlayerId, Data.GuestToken)` **before any other check or step**:

   ```csharp
   if (!(created is AuthCreateGuestResult.Success ok) || string.IsNullOrEmpty(ok.Data.GuestToken))
       return; // no guest exists yet: report the result
   await store.SaveGuestAsync(ok.Data.PlayerId, ok.Data.GuestToken); // app-owned storage
   if (string.IsNullOrEmpty(ok.Data.AuthorizationCode))
       return; // guest kept: restore it next time
   ```
3. **Saved credential:** call `auth.LoginGuestAsync(new GuestLoginRequest {
   GuestPlayerId, GuestToken, ClientId, DeviceKey, CodeChallenge,
   CodeChallengeMethod = CodeChallengeMethod.S256 })`.
4. Exchange `Data.AuthorizationCode` with the step 1 verifier and install the
   session as the Axyl session section describes. A missing code is unusable.
5. Return the login metadata and the guest credential to the app.

## Keep the guest recoverable

- Once creation returns a credential, every later exit keeps it: a missing code,
  a failed or unusable exchange, cancellation or a crash. The next attempt restores
  it with `LoginGuestAsync`; never create another guest because a later step failed.
- A failed restore never falls back to creation, never deletes the saved
  credential and never reports first-run success; return the typed outcome to the
  app. `InvalidGuestToken` can mean a provider was linked to this guest (the first
  link invalidates the guest token); the app decides recovery, such as provider
  login.
- `GrantKey` is a one-time key (60 s) that the app server gets from
  `/auth/v1/grant`. It is required when grant-key hardening is on and accepted when
  it is off (a sent key is always validated and consumed), so sending one is
  recommended. Never invent or replay a key; `GrantRequiredMissing` or
  `InvalidGrantKey` needs a fresh one.

## Verify

- [ ] No saved credential selects `CreateGuestAsync`, a saved one `LoginGuestAsync`;
  a failed restore never creates a guest.
- [ ] The created `(PlayerId, GuestToken)` is persisted before the code exchange and
  survives every later failure or cancellation.
- [ ] The code is exchanged once with the same attempt's verifier, followed by one
  `SetSession`.
- [ ] Typed, unknown, technical and cancelled results keep their meaning; a stale
  attempt never replaces a newer session.
- [ ] Refreshed session snapshots are persisted in order.
- [ ] Source review, compilation, test doubles and device/server runs are reported
  separately.

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

<!-- axyl-shared: core/auth-session.md -->

## Axyl session

### Setup and inputs

- Initialize once on the main thread with
  `HiveBootstrap.Initialize(config, b => b.AddAuth().AddToken())`; the default
  host is `https://core-api.hiveaxyl.com` (use `AddAuth(baseUrl)`/`AddToken(baseUrl)`
  only for a provisioned host). Call `AuthTokenRefresh.Enable(tokenHost, clientId)`
  once afterwards with the Token host. Never initialize inside a login.
- Resolve `IAuthService`, `ITokenService` and `ISessionManager`; if one is missing,
  stop before any auth call.
- `clientId` is the Axyl client ID, not a provider's. `deviceKey` is created once
  per device, persisted and reused: 22–64 printable ASCII (`^[!-~]{22,64}$`, UUID v4
  recommended); the SDK does not check it and the server rejects anything else.
- Each attempt uses a fresh PKCE pair (`CodeChallengeMethod.S256`, base64url
  SHA-256 of a random verifier). Keep the verifier for this attempt's exchange only.

### Authorization code to session

1. `tokens.IssueTokenAsync(new AuthorizationCodeTokenRequest { ClientId,
   AuthorizationCode, CodeVerifier }, ctx)`.
2. Continue only on `TokenIssueTokenResult.Success` with a nonempty `AccessToken`
   and `RefreshToken`. Expiry is Unix seconds now + `ExpiresIn`; if `ExpiresIn` is
   not positive, use the access token's JWT `exp`; with neither, the response is
   unusable.
3. Check cancellation, then call
   `session.SetSession(accessToken, refreshToken, playerId, expiresAtSec)` once. A
   failed, unknown, cancelled or superseded attempt never overwrites the current
   session.

`InvalidGrant`, `InvalidGrantExpired` and `InvalidGrantCodeChallenge` mean this
code or verifier is spent: start a new attempt, never replay the code.
`TemporarilyUnavailable` is the only retryable issue outcome: back off before
retrying (the interval is the app's choice). `InvalidClient` and `AppNotFound` are
configuration errors.

### Persistence and refresh

Subscribe to `session.OnSessionRefreshed` before `SetSession` and persist each
snapshot in order. Core refreshes a live session; never add a refresh loop.
`OnSessionExpired` means invalidation or an explicit clear: do not delete stored
credentials on app quit, transient or unknown failures, or storage `AccessDenied`.

<!-- /axyl-shared -->

<!-- axyl-shared: core/auth-account.md -->

## Login metadata

- `LoginResponseData` carries `PlayerId`, `CreatedAt`, `AuthorizationCode`,
  `ProviderList` (`ProviderId`, `ProviderUserId`, `ProviderIndex`) and `IsBlock`.
  Other responses carry only their own fields. Account creation
  (`GuestCreateResponseData`, `UsernameCreateResponseData`) returns `PlayerId`,
  `CreatedAt` and `AuthorizationCode` (guest also `GuestToken`), with no
  `ProviderList` or `IsBlock`. Token refresh returns tokens only, so earlier
  metadata stays stale and block status unknown. Never invent missing fields.
- Return the supplied fields in an app-owned result tied to that player and
  attempt; the SDK session keeps only tokens, player ID and expiry. The app decides
  what to persist; authorization codes stay transient.
- `ProviderList` lists the links at that response; it is not the provider catalog
  from `GetProviderListAsync`. `Guest` appears only for a pure guest. An empty list
  or a default value is not proof of no links.
- `CreatedAt` is not a new-player flag. `IsBlock` is account status for the app to
  handle, not a transport failure.

<!-- /axyl-shared -->
