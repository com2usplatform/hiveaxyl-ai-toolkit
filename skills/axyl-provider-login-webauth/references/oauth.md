# Google/X OAuth browser acquisition

## Google/X: configuration and redirect state

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

## Callback and exchange

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
