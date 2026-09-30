# Apple browser acquisition

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
