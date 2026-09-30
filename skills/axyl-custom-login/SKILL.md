---
name: axyl-custom-login
description: "Implements Hive Axyl Custom login in Unity using an app-server one-time grant key through PKCE, token exchange and session installation. Use for grant-key login and fresh-key recovery; the client does not obtain server credentials."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Custom login with an app-server grant

Signs in a player the game authenticated itself. The game's **server** calls
`/auth/v1/grant` with `authType=CUSTOM_LOGIN`, and the client submits only the
returned one-time key. The Installed SDK, SDK results, Axyl session and Login
metadata sections below apply to every step.

**Inputs:** a nonblank `grantKey`, Axyl `clientId` and `deviceKey`. The client never
holds the game's account password or any server credential.
**App owns:** the game's own login, its server integration, UI and result types.

## Flow

1. A blank key stops before any request.
2. New PKCE pair, then `auth.LoginCustomProviderAsync(new CustomLoginRequest {
   GrantKey, ClientId, DeviceKey, CodeChallenge,
   CodeChallengeMethod = CodeChallengeMethod.S256 }, ctx)`.
3. On `AuthLoginCustomProviderResult.Success`, exchange `Data.AuthorizationCode`
   with the same verifier and install the session. Grant acceptance alone is not
   a login.

## Rejected or uncertain keys

- `InvalidGrantKey`: ask the app server for a fresh key. Keys are single-use and
  live about 60 s; the server contract decides.
- Other typed or unknown outcomes are not fixed by a new key; report them. No
  outcome proves that the sent key is still unspent.
- After a timeout, failure or cancellation, never resend the same key or code; a
  new attempt needs a new key and a new PKCE pair.
- A failed attempt leaves the previous session and recovery data untouched.

## Verify

- [ ] A blank key makes no auth call; a valid attempt sends only the app-server key.
- [ ] The returned code is exchanged with the same attempt's verifier, followed by
  one `SetSession`.
- [ ] `InvalidGrantKey` requests a fresh key; other outcomes keep their meaning;
  nothing replays a key or a code.
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
