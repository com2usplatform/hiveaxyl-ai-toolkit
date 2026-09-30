# Android FCM

Register `AddFCM()` and resolve `Hive.Axyl.Push.Addon.FCM.IFCMPlugin` on Android,
with the app's Firebase configuration (`Assets/Plugins/Android/google-services.json`);
never invent credentials or project IDs.

1. Android API 33+: check `UnityEngine.Android.Permission.HasUserAuthorizedPermission`
   for `android.permission.POST_NOTIFICATIONS` and, if needed, call
   `Permission.RequestUserPermission` with `PermissionCallbacks` and wait for the
   grant or denial. This step is the app's; `IFCMPlugin` has no permission call.
   Lower API levels have no runtime ask, which is not advertising consent.
2. Denial stops before the token. After cancellation, a dialog that completes later
   must not continue the flow. An Editor branch reporting "granted" is a test path only.
3. `fcm.GetTokenAsync(ct)` must return `FcmServiceGetTokenResult.Success` with a
   nonempty `Data.Token`; register it with `UpsertTokenRequestProviderType.Fcm`.
4. Re-register on `TokenRefreshed` under the token renewal rules. `DeleteTokenAsync`
   is neither preparation, logout cleanup nor a retry for a failed registration.

Only when requested: `NotificationReceived` handles reception (a notification
Android shows in the background may not raise it), and cold start uses
`GetColdStartMessageAsync` with the installed launch-intent integration.
