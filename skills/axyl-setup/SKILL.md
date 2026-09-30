---
name: axyl-setup
description: "Sets up the Hive Axyl SDK in a Unity application: UPM package selection, bootstrap, capability and auth addon registration, service resolution, and automatic token refresh wiring. Use for installing or configuring Axyl, missing services, or initialization issues; login composition is handled by the relevant login flow skill."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Set up Axyl in Unity

Installs the needed packages and initializes Axyl once at startup, keeping the app's
existing configuration and registrations. The Installed SDK section below applies to
every step. Login, payment and push flows have their own skills; never initialize
inside them.

**Inputs:** `appId` and the Axyl `clientId` from app provisioning, the registry URL,
the selected login, payment and push routes, and any provisioned host.
**App owns:** the startup path, persistence policy and platform build settings.

## Install packages

Install from a scoped registry only: a `scopedRegistries` entry whose `scopes`
include `com.com2usplatform.hiveaxyl`, with the registry URL the developer supplies
(the SDK names `https://package.openupm.com` as its public registry); `steamworks`
also needs scope `com.rlabrecque`. Git URLs are unsupported because they bring no
dependency resolution. Keep a local `file:` distribution only when the developer
supplies it; its paths are relative to the manifest's directory, so check that each
target exists.

Declare every package the app calls. An addon depends only on core, never on its
module, so declare the module too (for example `push` with `push.addon.fcm`).
Install only the addons for the selected routes. The baseline requires Unity 6000.0+
and .NET Standard 2.1.

| Need | Package suffix after `com.com2usplatform.hiveaxyl.` | Supported target and minimum | Registration |
|---|---|---|---|
| Core | `core` | All SDK targets; Windows prerequisite below | `HiveBootstrap.Initialize` |
| Auth + token APIs | `auth` | All (server API) | **Both** `AddAuth()`, `AddToken()` |
| Secure persistence building block | `storage` | Android API 29+; Windows 11 or later on x64; iOS 17+; macOS 15+ on Apple silicon | `AddSecureStorage()`; app owns save/load policy |
| Apple sign-in | `auth.addon.apple` | iOS 17+; macOS 15+ on Apple silicon | `AddAppleSignIn()` |
| Google native account picker | `auth.addon.credentialmanager` | Android API 29+ | `AddCredentialManager()` |
| Play Games | `auth.addon.gpg` | Android API 29+ | `AddGooglePlayGames()` |
| Steam native | `auth.addon.steam`, `steamworks` | Windows 11 or later on x64; macOS 15+ on Apple silicon | `AddSteamAuth()`; inspect Steamworks.NET dependency |
| Google/X/Apple browser or Steam OpenID | `auth.addon.webauth` | Android API 29+; WebGL; Windows 11 or later on x64; iOS 17+; macOS 15+ on Apple silicon | `AddWebAuth()` |
| Payments Capability | `payments` | All (server API) | `AddPayments()` or `AddPayments(sandbox: true)` |
| Apple purchases | `payments.addon.apple` | iOS 17+; macOS 15+ on Apple silicon | `AddStoreKit()` |
| Google purchases | `payments.addon.google` | Android API 29+ | `AddPlayBilling()` |
| Steam purchase callbacks | `payments.addon.steam`, `steamworks` | Windows 11 or later on x64; macOS 15+ on Apple silicon | `AddSteamMicrotransactions()`; app initializes/pumps Steamworks |
| Push registry | `push` | All (server API) | `AddPush()` |
| Apple push | `push.addon.apns` | iOS 17+; macOS 15+ on Apple silicon | `AddAPNS()`; app supplies delegate forwarding |
| Android push | `push.addon.fcm` | Android API 29+ | `AddFCM()`; app supplies Firebase configuration |

Namespaces and assembly platform restrictions come from the installed package; Steam
extension visibility also needs platform compile guards. Other capability packages
(mailbox, serviceaccess, tcb, coupon, analytics) have their own registration. PG
payments use the Payments Capability and a browser, with no PG addon.

### Platform prerequisites

Match Player Settings and native deployment targets to each selected addon's minimum
before testing its route.

Every Windows Editor or player that loads Axyl needs the
[Microsoft Visual C++ 2015–2022 Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe),
and the game's installer must install it for players; Windows and Unity do not.
`core` links against it, so this applies even without secure storage or WebAuth. An
older redistributable lacks `VCRUNTIME140_1.dll`. Without it, initialization fails
with a `DllNotFoundException` for the `HiveAxyl_Core` native plugin.

## Initialize once

Call `HiveBootstrap.Initialize` once on the Unity main thread; a second call throws
`InvalidOperationException`. Each capability picks its host when it registers;
`Zone`/`SetZone` no longer exist.

| Registration | Default host |
|---|---|
| `AddAuth()`, `AddToken()` | `https://core-api.hiveaxyl.com` |
| `AddPush()` | `https://app-api.hiveaxyl.com` |
| `AddPayments()` | `https://commerce-api.hiveaxyl.com` |
| `AddPayments(sandbox: true)` | `https://sandbox-commerce-api.hiveaxyl.com` |

Only Payments has a sandbox; asking another capability for one does not compile.
`AddX(baseUrl)` is for an explicitly provisioned host: ask for it, never guess.

Example for an app using the payments sandbox and automatic session refresh:

```csharp
using Hive.Axyl.Auth;
using Hive.Axyl.Core;
using Hive.Axyl.Core.Unity;
using Hive.Axyl.Payments;
using Hive.Axyl.Storage;

// Run once on Unity's main thread. appId/clientId come from app provisioning.
const string tokenHost = "https://core-api.hiveaxyl.com"; // AddToken() default
var config = CoreConfig.CreateBuilder(appId)
    .SetAutoRefresh(true)
    .Build();
HiveBootstrap.Initialize(config, b => b
    .AddAuth()
    .AddToken()
    .AddPayments(sandbox: true)
    .AddSecureStorage());
AuthTokenRefresh.Enable(tokenHost, clientId);
```

`AuthTokenRefresh.Enable(string baseUrl, string clientId)` runs once, **after**
`Initialize`, with the Token host and the Axyl client ID; `AddToken` alone does not
wire refresh. The SDK refreshes live sessions: never race it with a manual refresh.

Register the selected addons in the same closure. In the Editor or off-platform a
registration may be a no-op, so a compiling `AddX` call does not prove the route
works. A missing native library can make `AddSecureStorage()` throw: guard it if the
app should start without secure storage. Resolve optional ports with
`HiveCore.TryResolve<T>(out var service)`, report a missing route and let the app
choose another; never turn a failed provider login into guest creation.

## Connect app state

- `IAuthService`, `ITokenService` and `ISessionManager` must resolve after setup; a
  missing one is a setup failure.
- Auth APIs do not install a session: the login flow exchanges the code and calls
  `ISessionManager.SetSession` with the validated tokens.
- Subscribe to `ISessionManager.OnSessionRefreshed` before login and persist each
  snapshot in order, rotated refresh tokens included, so an older save never
  overwrites a newer one.
- `ISecureStorage` is a mechanism, not automatic persistence; handle `AccessDenied`
  without clearing data. WebGL lacks the same guarantees: use the app's session-only
  or supported policy, never PlayerPrefs for secrets.
- `OnSessionExpired` and `ClearSession()` are destructive. Do not delete stored
  credentials on app quit, transient or unknown failures, a missing refresh token
  alone or `AccessDenied`; ending the in-memory session is not destroying recovery
  data.
- SDK events arrive on the main thread, but an awaited call resumes on the caller's
  context: dispatch Unity API access when needed. Logging such as `SetAllowlist` is
  optional.

## Verify

- [ ] Resolved packages share one release; required services resolve; a second
  initialization and a missing addon are handled.
- [ ] Each capability uses its intended host (sandbox only for Payments when asked),
  and refresh uses the Token host.
- [ ] Deployment targets meet each selected addon's minimum; Windows runs in the
  Editor and in a clean x64 player with the redistributable in the installer.
- [ ] A session refresh updates app persistence; Editor or test-double checks are
  reported separately from device and server runs.

<!-- axyl-shared: core/installed-sdk.md -->

## Installed SDK

- Read `Packages/manifest.json`, the lock file and each resolved `package.json`.
  All `com.com2usplatform.hiveaxyl.*` packages must be the same release (UPM does
  not enforce this); `com.hive.axyl.*` packages are a release before 1.0.0-rc.9.
- The installed SDK wins for APIs, types and contracts. If its release differs
  from this skill's `sdk-version`, apply a step only after its fields, result
  variants, platform support and failure behaviour match; otherwise stop at that
  step and report what is missing. Never change the installed version.
- The app owns UI, storage, the device key and orchestration. Sample and recipe
  classes are not SDK APIs.

<!-- /axyl-shared -->
