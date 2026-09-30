# Native Steam credentials for linking

The app initializes Steamworks: `SteamAPI.Init()` once and `SteamAPI.RunCallbacks()`
every frame; the SDK does neither.

1. Register `AddSteamAuth()` behind the package's platform guards and resolve
   `ISteamPlugin` with `HiveCore.TryResolve`; if it is unavailable, this route ends.
2. `steam.GetAuthTicketForWebApiAsync(new GetAuthTicketForWebApiRequest {
   Identity = configuredIdentity }, ct)`. `NotAuthenticated` means the player must
   sign into the Steam client first.
3. On `SteamServiceGetAuthTicketForWebApiResult.Success`, link with `Provider.Steam`,
   `ProviderToken = Data.TicketHex` and `ProviderUserId` = the app's SteamID64. The
   recipe allows an empty SteamID but leaves server acceptance unconfirmed: never
   fabricate one, and omit it only after confirming the server accepts that.
4. Keep the ticket and its plugin until the link settles (success, failure or
   cancellation), then call `steam.ReleaseTicket(ticketHex)` on the Unity main
   thread. Plugin disposal is only a shutdown backstop.

This is the native ticket, not the browser OpenID assertion.
