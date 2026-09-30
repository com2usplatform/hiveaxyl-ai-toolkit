# Google Play Games credentials for linking

Requires the Google **web** client ID and the redirect URI registered on that same
web OAuth client.

1. Register `AddGooglePlayGames()` and resolve `IGooglePlayGamesPlugin` with
   `HiveCore.TryResolve`; if it is unavailable, this route ends.
2. `IsAuthenticatedAsync(new IsAuthenticatedRequest(), ct)`. Only an explicit
   `GooglePlayGamesServiceIsAuthenticatedResult.NotAuthenticated` leads to
   `SignInAsync(new SignInRequest(), ct)`, which must succeed; unknown or error
   results are not "not authenticated".
3. `RequestServerSideAccessAsync(new RequestServerSideAccessRequest {
   WebClientId = googleWebClientId, ForceRefreshToken = configuredForceRefreshToken }, ct)`;
   require `Success` with a nonempty `Data.ServerAuthCode`.
4. `auth.ExchangeProviderTokenAsync(new ProviderTokenRequest {
   ProviderId = Provider.GooglePlayGames, ProviderCode = serverAuthCode,
   RedirectUri = googleWebRedirectUri }, new ApiCallContext { Token = ct })`, with no
   `CodeVerifier`. The SDK requires `RedirectUri` for Play Games: the URI registered
   on the web OAuth client passed as `WebClientId`. The flow never navigates there,
   but Google checks it during the exchange; a missing value stops the flow and is
   never invented.
5. On `AuthExchangeProviderTokenResult.Success`, link with `Provider.GooglePlayGames`,
   `Data.ProviderToken` and `Data.ProviderUserId`.

The recipe omits `RedirectUri`; follow the SDK contract.
Keep exchange-specific typed failures and cancellation distinct. The reviewed
sources contain no device run of this route.
