# APNs

Register `AddAPNS()` and resolve `Hive.Axyl.Push.Addon.APNS.IAPNSPlugin` on iOS or
macOS. The push entitlement and native delegate forwarding belong to the app; the
addon does not install the app delegate.

## Forwarding

Before `GetTokenAsync`, forward the native callbacks to the port:
`didRegisterForRemoteNotifications` passes the **device-token bytes** to
`NotifyDidRegisterForRemoteNotificationsAsync(byte[], ct)`, and a failure passes its
description to `NotifyDidFailToRegisterAsync(errorDescription, ct)`. Decode a hex
string from a native bridge into bytes; never send its UTF-8 bytes. Build the
forwarder from the installed SDK's template; the sample's
`ApnsRemoteNotificationForwarder` is an app example, not an SDK type.

Unity Mobile Notifications re-points the notification-center delegate without
chaining whenever it asks for permission, for push or local notifications, including
an implicit ask while scheduling. After every such ask, re-run the forwarder's
`Install` in a `finally` path (success, failure and cancellation); the template
re-chains only when replaced, so extra calls are no-ops.

## Permission, environment and token

1. Permission is OS-wide and shared with local notifications, so the app picks one
   owner. SDK route: `RequestAuthorizationAsync(options, ct)` with app-chosen
   `UNAuthorizationOption` values; on `ApnsServiceRequestAuthorizationResult.Success`,
   `Data.Granted == false` stops. The recipe's iOS route uses Unity Mobile
   Notifications instead: read `AuthorizationStatus` (`Authorized`, `Provisional`
   and `Ephemeral` are granted, `Denied` is denied) and ask only when undetermined,
   with an `AuthorizationRequest` for Alert/Badge/Sound and
   `registerForRemoteNotifications: false`, then apply the reinstall rule. On macOS
   the recipe uses the addon.
2. `GetProviderEnvironmentAsync(ct)` must succeed with a usable environment:
   `ProviderEnvironment.ApnsSandbox` maps to `UpsertTokenRequestProviderType.ApnsSandbox`
   and `ProviderEnvironment.Apns` to `UpsertTokenRequestProviderType.Apns`. Never
   infer production from null, an unknown value, the Editor, debug mode or a build name.
3. `GetTokenAsync(ct)` must return `ApnsServiceGetTokenResult.Success` with a
   nonempty `Data.Token`. Missing forwarding is diagnosed, never replaced by a
   synthesized token.

## Reception and cold start

Only when requested: forward `willPresent` and the notification response through
`NotifyWillPresentNotificationAsync` and `NotifyDidReceiveResponseAsync`, subscribe
to `NotificationPresented` and `NotificationOpened`, keep the app's delegate chain
and tell remote from local notifications. The forwarder template (since
1.0.0-rc.8) relays a remote `willPresent` and answers the OS itself with
`kAxylApnsForegroundOptions`, so the app's or Unity's `willPresent` is not called
for remote pushes; local notifications and taps still chain. Replace older template
copies, and change remote foreground presentation by editing that constant.

For cold start, capture the launch payload before startup, forward its raw JSON with
`NotifyColdStartNotificationAsync` and await that before the single-use
`GetColdStartNotificationAsync`. On macOS the capture must be compiled into the
launch app.
