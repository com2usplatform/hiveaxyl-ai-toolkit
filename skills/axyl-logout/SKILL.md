---
name: axyl-logout
description: "Implements user-requested Hive Axyl logout in Unity, including outcome-specific local cleanup, stored credentials and protection against clearing a replacement session. Does not implement account withdrawal, provider sign-out or automatic cleanup after login failure."
license: Apache-2.0
metadata:
  author: Com2uS Platform Corporation
  sdk-version: 1.0.0
  engine: Unity 6000.0+
---

# Log out the intended Axyl session

A user-requested logout of the current player. The Installed SDK and SDK results
sections below apply to every step; Push settings and account binding applies when
the app uses push.

**Inputs:** the live session the user asked to end.
**App owns:** coordination with login and refresh, storage, push policy and result types.

## Flow

1. Resolve `IAuthService` and `ISessionManager` and require the target live session.
   A missing service, no session or cancellation before the call ends here with
   nothing cleared; it is not a logout `Failure`.
2. If the app detaches push on logout, dispatch the detach first under this account
   (see Logout and account switch below) and keep its outcome separate.
3. Capture the target session, then call
   `auth.LogoutPlayerAsync(new ApiCallContext { Token = ct })` once.
4. Apply the returned result; cancellation after a returned `Success` does not undo it:

| `AuthLogoutPlayerResult` | Local state |
|---|---|
| `Success` | Clear the target session and its stored credentials; server invalidation confirmed |
| `Failure` with `Problem.Code == HiveErrorCode.Cancelled` | Keep; the caller withdrew the request |
| Other `Failure` | Clear the target's local state for this explicit logout; report server invalidation as unconfirmed |
| `GuestSignoutBlocked`, `TerminateService`, `PlayerNotFound` or another typed refusal | Keep; never bypass the server's refusal |
| Unknown | Keep |

5. Before `session.ClearSession()` or deleting storage, confirm the target is still
   the current session. Never erase a newer sign-in; a refresh that changed the token
   needs reconciliation, not blind deletion. One cleanup owner handles
   `OnSessionExpired` (raised by `ClearSession`), storage deletion and in-flight
   snapshot writes.
6. Report the server outcome, local cleanup and any replacement separately. A
   storage deletion failure means a restart may still log in automatically.

The recipe keeps local state on a technical failure; follow the SDK policy above.
That cleanup applies only to an explicit logout, not to a failed login, account
withdrawal or shutdown. `GuestSignoutBlocked` protects a guest's last recovery path.
Provider sessions (Apple, Google, Steam) are not signed out.

## Verify

- [ ] Success and a network failure clear only the target; cancellation, typed
  refusals and unknown results keep everything.
- [ ] A login completing during the request, a refresh during logout and a late
  snapshot write never lose the newer session.
- [ ] A storage deletion failure is reported rather than hidden by memory cleanup.
- [ ] With push: the detach runs under the original account before logout, and a
  detach accepted before an Auth refusal is reported as split state.

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

<!-- axyl-shared: core/push-management.md -->

## Push settings and account binding

Use `Hive.Axyl.Push.IPushService` with the account's authenticated session and the
device token actually registered; a login access token is not a device token. The
recipes do not compose these calls: the coordination below is the app's design.

| Change | Call with `new ApiCallContext { Token = ct }` |
|---|---|
| Language | `PatchTokenLanguageAsync(new PatchTokenLanguageRequest { Token = deviceToken, Language = language }, ctx)` |
| Consent | `PatchTokenAgreementAsync(new PatchTokenAgreementRequest { Token = deviceToken, Agreement = new Agreement { Info = info, Advertise = advertise, Night = night } }, ctx)` |
| Player binding | `DetachTokenIdentifierAsync(new DetachTokenIdentifierRequest { Token = deviceToken }, ctx)` |

Each result has `Success`, `ResourceNotInScope`, `InvalidSubject`, unknown and
`Failure` variants. `Success` means the server accepted the change asynchronously,
not that it was applied or that delivery changed. Keep the latest desired state
after a failure; a typed refusal is no reason to resend it unchanged.

- `Language` is a defined `LanguageCode`, never `Unspecified`.
- The consent patch replaces the whole `Agreement`; `Night = true` requires
  `Advertise = true`. Consent comes from app policy, never from OS permission.
- A new registration or token uses the full `UpsertTokenAsync`; a patch changes one
  setting of a known registration. Run patches and upserts through one app-owned
  update flow that carries account, token and the latest full state, so an old
  result never marks a newer token synchronized. Client ordering does not prove
  server apply order after a timeout.

### Logout and account switch

Whether logout detaches the player binding, and whether a detach failure blocks
logout, is app policy: reuse it or ask the app developer, never add it silently.

| Policy | Boundary |
|---|---|
| Detach on logout | Capture the player and device token, pause queued upserts, and dispatch the detach while that account is still authenticated, before Auth logout; then apply the app's failure policy and the logout result |
| Keep the binding | The token keeps targeting that player; login alone does not rebind it, and an app rebind upserts with the new account and its consent |

Detach removes only the player ID from the registration: it does not delete the
token, revoke OS permission, reset consent or recall queued notifications. Never
send one account's cleanup as another, or retry it with an invalidated token. If the
detach succeeds but Auth logout is refused or cancelled, report that split state;
never rebind automatically or call it a rollback.

<!-- /axyl-shared -->
