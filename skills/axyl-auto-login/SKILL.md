---
name: axyl-auto-login
description: "Restores a Hive Axyl session at Unity app restart from saved access/refresh tokens. Use for auto login, per-call token validation, refresh recovery and credential-preservation decisions when no session is live. Does not implement guest-token login or a live refresh loop."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Auto login at restart

Restores a session at app restart, with no live session, from the saved access
token, refresh token and `PlayerId`. The Installed SDK, SDK results, Axyl session
and Login metadata sections below apply to every step.

**Inputs:** Axyl `clientId` and the saved `(AccessToken, RefreshToken, PlayerId)`.
A storage load failure, `AccessDenied` and "nothing saved" are different states;
none of them is a reason to overwrite stored credentials.
**App owns:** storage, the expiry margin, sign-in UI and result types.

## Flow

1. Nothing saved: return "no session" without SDK calls. A session is already
   live: keep it; Core refreshes it, so never spend the saved refresh token.
2. Route by the saved access token's JWT `exp`, which is only a hint (the recipe's
   30 s margin is an app choice). Usable: step 3. Missing, unreadable or expired:
   step 5 if a refresh token exists, otherwise ask for sign-in and keep the data.
3. New PKCE pair, then `auth.LoginWithAccessTokenAsync(new TokenLoginRequest {
   ClientId, CodeChallenge, CodeChallengeMethod = CodeChallengeMethod.S256 }, ctx)`
   with `ctx = ApiCallContext.WithAccessToken(saved.AccessToken)` and
   `ctx.Token = ct`. Never call `SetSession` before this request.
4. On `AuthLoginWithAccessTokenResult.Success`, require
   `Data.PlayerId == saved.PlayerId` (a mismatch stops with storage untouched),
   then exchange `Data.AuthorizationCode` and install the session.
5. Refresh route, only with no live session:
   `tokens.IssueTokenAsync(new RefreshTokenTokenRequest { ClientId,
   RefreshToken = saved.RefreshToken }, new ApiCallContext { Token = ct })`.
   Apply the Axyl session success checks and expiry rule, keep the saved
   `PlayerId`, then call `SetSession` and persist the new pair. The refresh token
   rotates: never replay the old one. Block status is unknown on this route.

After step 3, take the refresh route only for an expired or rejected access
token. That result has no typed variant: it is an
`IUntypedProblem` whose `Problem.Code` is `HiveErrorCode.Unauthenticated` (a 401
on the caller-supplied token, which never triggers the SDK's session refresh). A
player mismatch, a configuration refusal or an unknown result is not proof of
expiry; report it instead of trying another grant.

## Keep or discard stored credentials

| Result | Stored credentials |
|---|---|
| `TokenIssueTokenResult.InvalidGrantRefreshToken` | Rejected: require fresh sign-in and apply the SDK invalidation policy |
| `AuthLoginWithAccessTokenResult.PlayerNotFound` | Keep; not proof that the credentials are invalid |
| Technical failure, cancellation, unknown or configuration outcome | Keep; no verdict |
| Success with unusable tokens or expiry | Keep the old state; do not overwrite it |
| Missing refresh token or expired access token | Keep; that route cannot restore, which is no reason to delete |
| Player ID mismatch | Keep; stop before the exchange and ask for sign-in |

Recovery never clears a session accepted while it was pending: guard the commit
instead of calling `ClearSession` after an await. The recipe marks
`PlayerNotFound` stale and never tries the
refresh route after access validation fails; follow the SDK policy above instead.

## Verify

- [ ] Nothing saved makes no SDK call; a live session never triggers a manual refresh.
- [ ] Access-token login sends the saved token through `ApiCallContext` before any
  `SetSession`; a player mismatch stops before the exchange.
- [ ] The refresh route uses the returned pair and expiry, persists it, never replays
  the old refresh token and reports block status as unknown.
- [ ] Only `InvalidGrantRefreshToken` leads to fresh sign-in; every other failure
  keeps the stored credentials.
- [ ] Source review, compilation, test doubles and device/server runs are reported
  separately; the reviewed sources include no live-server run of the refresh route.

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
