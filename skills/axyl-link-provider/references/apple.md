# Apple credentials for linking

1. Register `AddAppleSignIn()` and resolve `IAppleSignInPlugin` with
   `HiveCore.TryResolve`; if it is unavailable, this route ends.
2. Generate a fresh unpredictable nonce and call `apple.LoginAsync(new
   AppleSignInServiceLoginRequest { NonceHash, RequestedScopes }, ct)` with
   `NonceHash` = the lowercase SHA-256 hex of the nonce and app-selected scopes.
3. On `AppleSignInServiceLoginResult.Success`, link with `Provider.SigninApple`,
   `ProviderToken = Data.IdentityToken` and `ProviderUserId = Data.UserIdentifier`.
   A missing token or ID is unusable; dismissal is a cancellation.

Apple's authorization code is never an Axyl authorization code. The recipe does not
compare the ID token's nonce claim: keep the nonce if the app validates that claim,
and never claim the token is validated. Apple entitlements and provider
configuration are app prerequisites.
