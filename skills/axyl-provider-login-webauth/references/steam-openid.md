# Steam browser OpenID acquisition

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
