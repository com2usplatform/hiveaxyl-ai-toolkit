# Google Credential Manager credentials for linking

Requires the Google **web** client ID (not the Axyl client ID) and an APK signed with
the certificate registered for the Google Android OAuth client.

1. Register `AddCredentialManager()` and resolve `IAndroidCredentialManagerPlugin`
   with `HiveCore.TryResolve`; if it is unavailable, this route ends.
2. Generate a fresh raw nonce and call `credentials.LoginAsync` with
   `LoginRequest.Options` holding a `CredentialOption` whose `SignInWithGoogle =
   new SignInWithGoogleOption { WebClientId = googleWebClientId, Nonce = nonce }`.
3. On `AndroidCredentialManagerServiceLoginResult.Success`, read
   `Data.Selected.GoogleIdToken`. Require a nonempty `IdToken` and `UniqueId` and an
   ID token `nonce` claim equal to the raw nonce; this is correlation, not signature
   verification.
4. Link with `Provider.Google`, `ProviderToken = IdToken` and
   `ProviderUserId = UniqueId`.

No browser or provider-code exchange happens on this route. A missing `UniqueId` is
a native-library or build problem: never guess an ID or switch routes. The reviewed
sources contain no device run of this route.
