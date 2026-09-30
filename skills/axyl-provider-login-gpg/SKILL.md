---
name: axyl-provider-login-gpg
description: "Implements Google Play Games sign-in through a Hive Axyl session in Unity on Android. Use for IsAuthenticated, SignIn, serverAuthCode acquisition and provider exchange with the web OAuth client's registered redirect URI. Ordinary Google account sign-in uses another route."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Google Play Games login (Android)

Play Games sign-in and server-side access, a provider-token exchange, then the
Axyl provider join and session.
The Installed SDK, SDK results, Axyl session, Login metadata and Provider join
sections below apply to every step.

**Inputs:** the Google **web** client ID, the redirect URI registered on that same
web OAuth client, Axyl `clientId` and `deviceKey`.
**App owns:** Play Games and Google project configuration, UI and result types.

## Flow

1. Register `AddGooglePlayGames()` and resolve `IGooglePlayGamesPlugin`
   (`Hive.Axyl.Auth.Addon.GPG`) with `HiveCore.TryResolve`; if it is unavailable,
   this route ends.
2. `IsAuthenticatedAsync(new IsAuthenticatedRequest(), ct)`. Only an explicit
   `GooglePlayGamesServiceIsAuthenticatedResult.NotAuthenticated` leads to
   `SignInAsync(new SignInRequest(), ct)`, which must succeed; unknown or error
   results are not "not authenticated".
3. `RequestServerSideAccessAsync(new RequestServerSideAccessRequest {
   WebClientId = googleWebClientId, ForceRefreshToken = configuredForceRefreshToken }, ct)`;
   require `Success` with a nonempty `Data.ServerAuthCode`.
4. `auth.ExchangeProviderTokenAsync(new ProviderTokenRequest {
   ProviderId = Provider.GooglePlayGames, ProviderCode = serverAuthCode,
   RedirectUri = googleWebRedirectUri }, ctx)`, with no `CodeVerifier`. The SDK
   requires `RedirectUri` for Play Games: the URI registered on the web OAuth client
   passed as `WebClientId`. The flow never navigates there, but Google checks it
   during the exchange; a missing value stops the flow and is never invented.
5. On `AuthExchangeProviderTokenResult.Success`, join with
   `Provider.GooglePlayGames`, `Data.ProviderToken` and `Data.ProviderUserId`.

The recipe omits `RedirectUri`; follow the SDK contract.
Keep exchange-specific typed failures and cancellation distinct.

## Verify

- [ ] Only explicit `NotAuthenticated` triggers sign-in; server-side access receives
  the configured web client ID and refresh flag.
- [ ] The exchange sends the nonempty `ServerAuthCode` with the configured
  web-client redirect URI; a missing value stops before the exchange.
- [ ] The exchange result feeds `Provider.GooglePlayGames` with a fresh Axyl PKCE pair.
- [ ] Device and live-server checks are reported as unverified unless run; the
  reviewed sources contain no device run.

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

<!-- axyl-shared: core/provider-join.md -->

## Provider join

Turns an acquired provider credential into an Axyl session. Acquisition, and any
provider-code exchange, must have succeeded first; a cancelled, failed or unknown
acquisition stops before this join.

| Route | `Provider` | `ProviderToken` | `ProviderUserId` |
|---|---|---|---|
| Apple native | `SigninApple` | `IdentityToken` | `UserIdentifier` |
| Google Credential Manager | `Google` | `IdToken` | `UniqueId` |
| Google/X/Apple browser, Play Games | `Google`, `X`, `SigninApple`, `GooglePlayGames` | `ProviderToken` from `ExchangeProviderTokenAsync` (direct exchange: Google `id_token`, X access token) | its `ProviderUserId` (direct exchange: `sub`, `data.id`) |
| Steam native | `Steam` | `TicketHex` | the app's SteamID64; confirm server support before omitting it |
| Steam OpenID | `Steam` | the callback query without the leading `?` or fragment, bytes unchanged | SteamID64 from `openid.claimed_id` |

Never cast another enum to `Provider` by number.

1. New Axyl PKCE pair, separate from any provider OAuth PKCE or state.
2. `auth.LoginProviderAsync(new ProviderLoginRequest { ProviderId, ProviderUserId,
   ProviderToken, ClientId, DeviceKey, CodeChallenge,
   CodeChallengeMethod = CodeChallengeMethod.S256 }, ctx)`.
3. On `AuthLoginProviderResult.Success`, exchange `Data.AuthorizationCode` with this
   Axyl verifier and install the session.

`ProviderTokenError`, `ProviderConfigNotFound`, `ProviderClientInfoNotExists`,
`ProviderRequestFailed` and app, service or IP outcomes keep their own meaning;
never switch route or create a guest because of them. Login has no typed
`ProviderNotSupported`: that code arrives as `IUnknownOutcome`. Show block UI only
from `IsBlock`. A native Steam ticket stays alive until backend validation settles,
then its owner releases it on the main thread.

<!-- /axyl-shared -->
