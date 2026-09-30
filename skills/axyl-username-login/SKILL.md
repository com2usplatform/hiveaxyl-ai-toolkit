---
name: axyl-username-login
description: "Implements Hive Axyl username/password login and app-requested login-or-signup in Unity, including password transformation, restricted signup fallback, PKCE and session installation."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Username login or signup

Signs in with a username and password and, only when the app asks for
login-or-signup, creates the account when sign-in fails. The Installed SDK, SDK
results, Axyl session and Login metadata sections below apply to every step.

**Inputs:** Axyl `clientId`, `deviceKey`, username, the exact typed password and,
for signup, an optional app-server grant key.
**App owns:** whether signup is offered, UI and result types.

## Flow

1. Password is the lowercase hex SHA-256 of the **exact** UTF-8 input (no trim,
   case kept). The SDK sends the string as given; never send or log the raw
   password.
2. New PKCE pair, then `auth.LoginUsernameAsync(new UsernameLoginRequest {
   Username, Password = passwordHash, ClientId, DeviceKey, CodeChallenge,
   CodeChallengeMethod = CodeChallengeMethod.S256 }, ctx)`. On Success, exchange
   `Data.AuthorizationCode` and install the session.
3. Sign up only when the app requested it and the result is
   `AuthLoginUsernameResult.UsernameVerifyFailed` (unknown username **or** wrong
   password): new PKCE pair, then `auth.CreateUsernameAsync(new
   UsernameCreateRequest { Username, Password = passwordHash, ClientId,
   DeviceKey, CodeChallenge, CodeChallengeMethod = CodeChallengeMethod.S256,
   GrantKey = grantKeyOrNull }, ctx)`. A missing key is `null`; an empty string is
   sent and refused.
4. On `AuthCreateUsernameResult.Success`, mark the result as a new account and
   exchange its code with the **signup** verifier. `UsernameAlreadyExists` means
   the password was wrong: report incorrect credentials and never sign up again.
5. Any other result stops at its own stage. Return new-account and block status
   separately.

## Rules

- The grant key is one-time (60 s) and comes from the app server's
  `/auth/v1/grant`. It is required when grant-key hardening is on and accepted
  when it is off (a sent key is always validated and consumed), so sending one is
  recommended. The recipe comment says to omit it when hardening is off; follow
  the SDK. `GrantRequiredMissing` or `InvalidGrantKey` needs a fresh key; never
  invent or replay one.
- Login-or-signup can create an account for a mistyped new username; expose the
  new-account result so the UI can show it.
- A failed or cancelled exchange after signup does not undo the account. The
  username and password remain the way back, and a retry starts again with a new
  PKCE pair.
- Unrelated failures never erase a live session or stored recovery data.

## Verify

- [ ] The hash keeps whitespace, case and UTF-8 and is lowercase SHA-256 hex; no raw
  password is sent or logged.
- [ ] Only `UsernameVerifyFailed` enters signup, only when requested, with a fresh
  PKCE pair; login-only never creates an account.
- [ ] `UsernameAlreadyExists` and other failures never loop signup; a missing grant
  key is `null`.
- [ ] Each code is exchanged with the verifier of the call that returned it; a
  failure after signup keeps the new-account result without reporting login.
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
