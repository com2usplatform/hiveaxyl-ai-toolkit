---
name: axyl-provider-login-webauth
description: "Implements browser provider login through a Hive Axyl session in Unity: Google/X OAuth, Sign in with Apple on Android/Windows/WebGL and Steam OpenID. Use for WebAuth callbacks, redirect/loopback/state, the Axyl relay, provider exchange and Axyl handoff. Native Apple on iOS/macOS, Credential Manager, GPG and Steam tickets use their native routes."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Browser provider login (Google/X OAuth, Apple, Steam OpenID)

Browser acquisition through the WebAuth addon, then the Axyl provider join and
session. The Installed SDK, SDK results, Axyl session, Login metadata, Provider
join and Browser acquisition prerequisites sections below apply to every step.

**Inputs:** Axyl `clientId`, `deviceKey`, the Axyl app ID for relayed callbacks and
the provider configuration: authorize endpoint, client ID (Apple: the Services ID),
scope, registered redirect or return URL and any relay.
**App owns:** provider registration, the callback page, UI and storage.

Read only the requested provider's procedure:

| Provider | Read | Covers |
|---|---|---|
| Google or X | [OAuth](references/oauth.md) | redirect and loopback URIs, state, callback, provider-code exchange |
| Apple on Android, Windows or WebGL | [Apple](references/apple.md) | Services ID, Axyl relay, routing prefix on `state`, server-side exchange without provider PKCE |
| Steam without the native client | [Steam OpenID](references/steam-openid.md) | return URL, Axyl relay and app callback, assertion checks, join inputs |

Keep the selected mode, redirect and state together through acquisition; a
cancellation or state mismatch stops before the join. Provider PKCE and Axyl PKCE
are separate.

## Verify

- [ ] Google/X: state is validated before reading code or error; authorize and
  exchange use the same redirect URI; the exchange mode never switches silently.
- [ ] Loopback: the redirect is allocated before opening, and a relay's state prefix
  is handled as configured.
- [ ] Android: `hiveAxylWebAuthRedirectScheme` is set in `launcherTemplate.gradle`
  and a real redirect reaches the `OpenAsync` callback.
- [ ] Apple: `state` carries the platform's routing prefix and is compared with
  `realState` first; the exchange sends the relay URL and no `CodeVerifier`;
  `user_cancelled_authorize` is a cancellation.
- [ ] Steam OpenID: mode, return URL and claimed ID are validated, the assertion
  bytes are preserved and no OAuth exchange runs; on iOS/Android `return_to` is the
  relay with `relayTo` and a fresh `s`.
- [ ] Relayed callbacks: `OpenRequest.RedirectUri` is `{appId}://oauth-callback`
  with the Axyl app ID, Android registers that scheme on the callback Activity, and
  a real callback reaches the app on iOS and Android.
- [ ] WebGL keeps the originating user gesture; real callback, bridge and server
  validation are reported separately from simulated callbacks.

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

<!-- axyl-shared: auth/browser.md -->

## Browser acquisition prerequisites

Require `AddWebAuth()` and a resolved `IExternalUserAgent` on the target
player. Google/X OAuth, Apple and Steam OpenID differ in configuration, callback
validation and exchange; apply only the selected provider's procedure.

### App prerequisites

WebGL must open the popup in the originating user gesture; do not insert an
unrelated await before `OpenAsync`. The app ships a callback page compatible
with the SDK bridge and origin checks. The sample's file/hosting layout is an
example; a usable registered callback and bridge integration are requirements.
On Android, set `hiveAxylWebAuthRedirectScheme` in the app module's
`launcherTemplate.gradle` to the scheme of `OpenRequest.RedirectUri`. Do not put
it in `mainTemplate.gradle`; the application module must resolve the library's
placeholder. A second callback scheme (such as the Axyl relay's app callback next to
an OAuth redirect scheme) needs its own intent-filter on the same WebAuth callback
Activity, declared in an app-owned Android library manifest. Verify that a real
Android redirect reaches the `OpenAsync` callback. Endpoints, UI and credential-source
class design remain app choices.

### Axyl relay

Steam on iOS/Android and Apple outside iOS/macOS return through the relay Axyl
operates at `relayBase` = `{baseUrl}/auth/v1/provider/callback`, where `{baseUrl}` is
the Axyl server host. The app's own callback is `appCallback` =
`{appId}://oauth-callback` with the **Axyl app ID**, not the Android package name
(the relay answers a package name with `app_not_found`). Pass `appCallback` as
`OpenRequest.RedirectUri`, never the relay URL. iOS matches that scheme itself;
Android needs it registered as above; WebGL and Windows loopback use their own
callback and no app scheme. The app still checks that the callback it received is
the one this attempt expected.

<!-- /axyl-shared -->
