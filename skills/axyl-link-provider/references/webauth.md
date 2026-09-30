# Browser credentials for linking

## Contents

- Linking handoff
- Browser acquisition prerequisites
- Google/X OAuth browser acquisition: configuration and redirect state, callback
  and exchange
- Apple browser acquisition
- Steam browser OpenID acquisition

## Linking handoff

Follow the browser sections below for Google/X OAuth (`Provider.Google` or
`Provider.X`), Apple (`Provider.SigninApple`) or Steam OpenID (`Provider.Steam`),
including their state, redirect
and provider-exchange rules. Hand the acquired token and user ID to
`ProviderLinkRequest` instead of the login join: no Axyl login PKCE,
`LoginProviderAsync`, Axyl code exchange or new session.

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

## Google/X OAuth browser acquisition

### Google/X: configuration and redirect state

Require `AddWebAuth()`, `IExternalUserAgent`, provider authorize endpoint,
provider client ID, scope and registered redirect configuration.
These are app/provider provisioning values, not Axyl's client ID.
Choose server-mediated exchange or public-client direct exchange explicitly;
do not infer the mode from the OS alone.

Keep two URIs:
- `openUri`: redirect given to `IExternalUserAgent.OpenAsync`.
- `authorizeUri`: `redirect_uri` in the provider authorization request and
  repeated character for character in provider code exchange, including any
  `?relayTo=...` of the Hive callback relay; a mismatch fails as `invalid_grant`.

For a Windows loopback route, obtain
`(agent as WebAuthSessionPlugin)?.WindowsLoopback`; it is normally a property,
not a separately registered service. An app-supplied `IWindowsLoopbackAgent`
may instead be registered. Call
`AllocateLoopbackRedirectUriAsync(new AllocateLoopbackRedirectUriRequest {
PathPrefix = configuredPathPrefix }, ct)` before opening; retain the returned
`Data.RedirectUri` as `openUri`. Do not invent an unreserved port.

For providers accepting a variable loopback port, the recipe uses the allocated
origin as `authorizeUri`. For an explicitly configured hosted relay, use the
registered relay URI as `authorizeUri`, put `<allocated-port>:` before the
random state, and compare the callback to the state **after** the relay strips
that prefix. This is a relay contract, not a rule for arbitrary OAuth callbacks.
Without loopback, both URIs are the registered interceptable redirect.
A requested loopback flow with no allocator fails before opening.

### Callback and exchange

1. Generate a provider PKCE pair and fresh unpredictable state (32 random bytes,
   base64url, as in the recipe). Preserve them for this attempt.
2. URL-encode `response_type=code`, provider `client_id`,
   `redirect_uri=authorizeUri`, selected scope, state,
   `code_challenge` and `code_challenge_method=S256`.
3. `agent.OpenAsync(new OpenRequest { Url = authorizeUrl,
   RedirectUri = openUri }, ct)`.
4. On `ExternalUserAgentServiceOpenResult.Success`, inspect `Data.Parameters`.
   Compare returned `state` **before** reading either code or error.
   Mismatch stops the flow; never exchange a code from another attempt.
5. `error=access_denied` is user-declined consent. Other errors are reported
   distinctly. Require a nonempty `code` before exchange.
6. For server-mediated exchange call
   `auth.ExchangeProviderTokenAsync(new ProviderTokenRequest {
   ProviderId = Provider.Google /* or X */, ProviderCode = code,
   RedirectUri = authorizeUri, CodeVerifier = providerVerifier },
   new ApiCallContext { Token = ct })`. `RedirectUri` is required for Google
   and X; `CodeVerifier` is required for X and, for Google, whenever the
   authorize request carried `code_challenge` (always in this flow).
   Read `AuthExchangeProviderTokenResult.Success.Data.ProviderToken` and
   `ProviderUserId`.
7. For a configured **public-client direct exchange**, the app (not an Axyl API)
   POSTs form fields `grant_type=authorization_code`, `code`,
   `code_verifier`, provider `client_id`, and the same `redirect_uri` to
   its provisioned provider token endpoint. Do not embed a client secret.
   Google: require returned `id_token` and its nonempty `sub` as user ID.
   X: require `access_token`, then GET configured userinfo with that bearer and
   require `data.id`. Missing response fields or HTTP errors stop acquisition.
   Browser CORS/provider registration support must exist for direct exchange.
8. Feed the acquired credential to the common **Axyl** join with a fresh
   **Axyl** verifier/challenge. Provider code, verifier and client ID do not
   belong in `AuthorizationCodeTokenRequest`.

Caller cancellation during exchange is a technical `Cancelled`, distinct from
UI dismissal. Failed/unknown provider exchange never proceeds to login.
Do not switch exchange modes just to hide `ProviderClientInfoNotExists`;
verify the app's OAuth registration/configuration.

## Apple browser acquisition

For Android, Windows and WebGL; iOS and macOS use the native addon. Apple accepts no
loopback redirect, so every platform returns through the Axyl relay. Requires the
Apple **Services ID** as the provider client ID, with the relay URL registered as its
Return URL and the relay's domain as its domain. The `.p8` key is registered in the
Axyl console: the Axyl server builds the client secret and exchanges the code, so the
app holds neither and there is no direct exchange.

1. Create a fresh `realState` per attempt, without `|`. Choose `openUri` and the
   routing prefix the relay strips from `state`:
   - Windows: reserve a loopback redirect with `(agent as
     WebAuthSessionPlugin)?.WindowsLoopback.AllocateLoopbackRedirectUriAsync(new
     AllocateLoopbackRedirectUriRequest { PathPrefix = configuredPathPrefix }, ct)`;
     `openUri` is its `Data.RedirectUri`, and `state = "<port>:" + realState`.
   - Android: `openUri = appCallback`, and `state = appCallback + "|" + realState`.
   - WebGL: `openUri` is the HTTPS callback page on the player's origin that posts
     the result to the opener, and `state = openUri + "|" + realState`.
2. Build `https://appleid.apple.com/auth/authorize` with `response_type=code`,
   `client_id` = the Services ID, `redirect_uri` = the relay URL,
   `response_mode=form_post`, the chosen scope (`name email` to request them) and
   `state`, URL-encoding each value. Apple takes no provider PKCE.
3. `agent.OpenAsync(new OpenRequest { Url = authorizeUrl, RedirectUri = openUri },
   ct)`. The relay receives Apple's POST, strips the prefix and forwards `code` or
   the unchanged `error` with `realState`.
4. Compare the returned `state` with `realState` before reading anything else.
   `error=user_cancelled_authorize` is a cancellation (the recipe also treats
   `access_denied` as one); any other error, or a missing `code`, stops.
5. `auth.ExchangeProviderTokenAsync(new ProviderTokenRequest { ProviderId =
   Provider.SigninApple, ProviderCode = code, RedirectUri = relayUrl },
   new ApiCallContext { Token = ct })` with no `CodeVerifier`. `RedirectUri` is the
   relay URL from the authorize request, not `openUri`.
6. Join with `Provider.SigninApple` and the exchange's `ProviderToken` and
   `ProviderUserId`, using a fresh Axyl PKCE pair.

## Steam browser OpenID acquisition

When no native Steam client route is selected, the recipe uses WebAuth OpenID,
not OAuth code exchange. Keep two configured inputs:
- `openid.return_to`: the absolute HTTP(S) URL Steam returns to. Steam refuses a
  custom scheme, so on iOS/Android it is the Axyl relay:
  `{relayBase}?relayTo={URL-encoded appCallback}&s={fresh random per attempt}`
  (use `&` when `relayBase` already has a query). The relay keeps the `openid.*`
  query and redirects to `appCallback`.
- `OpenRequest.RedirectUri`: where the app itself receives the callback. It
  equals `return_to` when the platform captures that HTTP(S) redirect directly
  (Windows loopback, WebGL callback page), with no relay; behind the relay it is
  `appCallback`. iOS `ASWebAuthenticationSession` matches the callback by this
  scheme, so passing the relay URL waits silently and never completes.

Build the Steam OpenID 2.0 checkid_setup request with `openid.ns`,
`openid.mode=checkid_setup`, `openid.return_to`, `openid.realm` (return URL
origin), and both identity/claimed_id equal to the OpenID identifier_select URI.
Open `https://steamcommunity.com/openid/login` through `IExternalUserAgent`.

On callback: `openid.mode=cancel` means cancellation; otherwise require
`id_res`, `openid.return_to` exactly equal to the configured return URL, and a
Steam claimed identity shaped as
`https://steamcommunity.com/openid/id/<17 decimal digits>`.
Pass that SteamID64 (the last `claimed_id` segment) as `ProviderUserId` and the
assertion query string from `Data.CallbackUrl` as `ProviderToken` to the Steam
Axyl join. Remove the leading `?` and any URL fragment; preserve the
remaining query bytes without decoding/re-encoding them.
These checks correlate/parse the assertion; the **server** must perform OpenID
authentication verification. Do not replace it with local claim parsing.
