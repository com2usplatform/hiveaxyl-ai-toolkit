---
name: axyl-link-provider
description: "Links a provider account to the signed-in Hive Axyl player in Unity. Use for guest-to-provider linking, acquisition, ownership conflicts and post-link reconciliation while preserving the current account. Does not implement provider login or account merging."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Link a provider to the current player

Adds a provider account to the signed-in player without changing the session. The
Installed SDK, SDK results and Login metadata sections below apply to every step.

**Inputs:** a live session and the chosen route's configuration, or an
already-acquired token and user ID with their `Provider` value.
**App owns:** UI, storage, conflict choices and result types.

## Flow

1. Resolve `IAuthService` and `ISessionManager` and require a live session before
   opening provider UI; check cancellation.
2. Capture the originating player and session. The recipe keeps `session.AccessToken`
   and aborts if it changed after acquisition, a refresh included; the app may tell a
   same-player refresh from an account change, but never links whichever account is
   current.
3. Acquire the credential with the chosen route below, or validate the supplied one.
   Dismissal, cancellation, an unknown result or a failure stops here.
4. Recheck the player, session and cancellation, then call
   `auth.LinkProviderAsync(new ProviderLinkRequest { ProviderId = provider,
   ProviderUserId = providerUserId, ProviderToken = providerToken },
   new ApiCallContext { Token = ct })`, coordinated so an account change cannot
   retarget it. Linking never calls `LoginProviderAsync`, exchanges an Axyl code or
   calls `SetSession`.
5. On `AuthLinkProviderResult.Success`, require `Data.PlayerId` and
   `Data.ProviderUserId` and check them against the intended player and credential.
   The first provider link invalidates that player's guest token: retire a saved
   guest credential only when its player ID matches, and keep other players'.

| Route | `Provider` | Read |
|---|---|---|
| Sign in with Apple | `SigninApple` | [Apple](references/apple.md) |
| Google Credential Manager (Android) | `Google` | [Credential Manager](references/credential-manager.md) |
| Google Play Games (Android) | `GooglePlayGames` | [Play Games](references/gpg.md) |
| Native Steam ticket | `Steam` | [Steam](references/steam.md) |
| Browser Google/X OAuth, Apple or Steam OpenID | `Google`, `X`, `SigninApple`, `Steam` | [WebAuth](references/webauth.md) |

Each route stops at the token and user ID. Register its addon (for example
`.AddAppleSignIn()`) in the app's single `HiveBootstrap.Initialize` builder next to
`AddAuth()`, never at link time. The addon namespaces are `Hive.Axyl.Auth.Addon.Apple`,
`.CredentialManager`, `.GPG`, `.Steam` and `.WebAuth`; a missing port or
configuration ends that route. Use the route's real `Provider`; never cast another
enum or default an unknown provider to `X`. A native Steam ticket stays alive
until the link settles, then its owner releases it.

## Conflicts

| `AuthLinkProviderResult` | Handling |
|---|---|
| `ProviderOwnedByOther` | Another player owns it: ask for the app's account choice; never switch or merge automatically |
| `ProviderTypeAlreadyExists` | This player already has that provider type: do not overwrite or retry |
| `ProviderAlreadyConnected` | This pair is already linked: reconcile instead of repeating the link |
| Anything else | Keep its meaning, the session and recovery data; it is not an ownership conflict |

Username linking has its own SDK contract and no recipe here; never send a password
as `ProviderToken`.

## Uncertain link

After a cancellation once dispatched, an unknown result or an `IUntypedProblem`, the
server may already have linked. A timeout has no dedicated result or error code: it
is one of these technical failures. Keep the guest credential and recovery data, and
do not retry blindly.

- `GetProviderListAsync` is the provider catalog for the app and country, not this
  player's links, so it cannot confirm the link. There is no linked-account read.
- A fresh successful login for the same player (for example
  `LoginWithAccessTokenAsync`) can confirm the exact `ProviderId` and
  `ProviderUserId` in its `ProviderList`. Never reauthenticate or install a session
  automatically; if the app chooses to, use its login flow and account guards. A
  guest re-login may fail once the link has invalidated the guest token.
- A different player, a match on provider type alone, a cached pre-link list or a
  cancelled wait confirms nothing and authorizes neither a retry nor a deletion.
  Report the gap when no confirmation is available.

## Verify

- [ ] No live session stops before provider UI; an account change during acquisition
  aborts the link.
- [ ] `LinkProviderAsync` receives the route's `Provider`, token and user ID; no
  login, code exchange or `SetSession` runs.
- [ ] The three conflicts stay distinct, with no automatic account switch.
- [ ] An uncertain result keeps the guest credential and is not reconciled from
  `GetProviderListAsync`; success retires only the matching player's guest credential.
- [ ] Steam tickets are released only after the link settles, when that route is used.

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

<!-- axyl-shared: core/results.md -->

## SDK results

Match each call's concrete result and read `Success.Data` only after checking the
fields the next step needs. The markers live in `Hive.Axyl.Contracts.Result`.

| Result | Handling |
|---|---|
| `IUserCanceledOutcome` | The user dismissed OS or provider UI: stop this attempt quietly |
| `IUnknownOutcome` | Keep `Code` and `RawJson`; never treat it as a known refusal or a success |
| `IUntypedProblem` | Technical failure in `Problem` (`HiveError`): network, timeout or caller `Cancelled` |
| Other typed variant | Only that call's documented meaning |

Pass `new ApiCallContext { Token = ct }` and check cancellation before each
follow-up call; a request cancelled in flight may still have taken effect. Never
branch on HTTP status, exception text or raw bodies, and never log tokens or
credentials.

<!-- /axyl-shared -->

<!-- axyl-shared: core/auth-account.md -->

## Login metadata

- `LoginResponseData` carries `PlayerId`, `CreatedAt`, `AuthorizationCode`,
  `ProviderList` (`ProviderId`, `ProviderUserId`, `ProviderIndex`) and `IsBlock`.
  Other responses carry only their own fields. Account creation
  (`GuestCreateResponseData`, `UsernameCreateResponseData`) returns `PlayerId`,
  `CreatedAt` and `AuthorizationCode` (guest also `GuestToken`), with no
  `ProviderList` or `IsBlock`. Token refresh returns tokens only, so earlier
  metadata stays stale and block status unknown. Never invent missing fields.
- Return the supplied fields in an app-owned result tied to that player and
  attempt; the SDK session keeps only tokens, player ID and expiry. The app decides
  what to persist; authorization codes stay transient.
- `ProviderList` lists the links at that response; it is not the provider catalog
  from `GetProviderListAsync`. `Guest` appears only for a pure guest. An empty list
  or a default value is not proof of no links.
- `CreatedAt` is not a new-player flag. `IsBlock` is account status for the app to
  handle, not a transport failure.

<!-- /axyl-shared -->
