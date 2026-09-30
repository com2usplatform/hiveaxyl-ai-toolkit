# Hive Axyl SDK Flow

> Read this only when SKILL.md determined that the repository uses the Hive Axyl SDK. Do not apply it together with the SDK v4 flow.

This document defines the integration gate, auto-collected properties, required property sending, and code generation differences
specific to Axyl. Event design follows the event design and code generation rules, and the send rules follow the SDK log send rules.

## 1. Integration gate

Per the official Axyl documentation, the currently supported game engine is Unity.
Do not generate Axyl code for anything other than Unity.
The gate does not verify the Unity version; judge instead on whether the installed Axyl package resolves correctly in the project and
is actually used in the code.

Judgment criteria:

| Item | Check criterion | Required |
|------|-----------|------|
| Game engine | Check ProjectSettings and the Unity project structure | Yes |
| UPM registration | The com.com2usplatform.hiveaxyl scope and the com.com2usplatform.hiveaxyl.core dependency in Packages/manifest.json, or an equivalent Git package declaration | Yes |
| Installation resolution | If Packages/packages-lock.json exists, confirm that com.com2usplatform.hiveaxyl.core actually resolved | Conditional |
| Namespace | Hive.Axyl.Core and Hive.Axyl.Core.Unity types imported or used with fully qualified names | Yes |
| App ID | A non-empty, real Axyl App ID passed to CoreConfig.CreateBuilder | Yes |
| Configuration completion | A Build call on the CoreConfig builder | Yes |
| Global initialization | HiveBootstrap.Initialize called exactly once in the app startup path | Yes |
| Module registration | The modules actually used registered in Initialize's assemble callback | Yes |

Do not use a specific version value in ProjectVersion.txt as an integration success or failure condition. If only the manifest.json
declaration is present, with no packages-lock.json and no Axyl type usage or initialization, report it as "package declaration only"
and do not judge the integration complete.

The initialization chain must connect in this order in the actual code.

    CoreConfig.CreateBuilder(<appId>)
    → Build()
    → HiveBootstrap.Initialize(config, assemble)

`SetXxx()` configuration calls between CreateBuilder and Build are optional and are not a gate criterion. The official
initialization documentation does not require `SetZone`, so do not judge the integration incomplete because there is no `SetZone` call.

Placeholders such as `<appId>`, `{appId}`, or an empty string are not a valid App ID. An Axyl App ID is an identifier created in the
Axyl console per runtime environment and store combination — do not treat it as the Android applicationId or the iOS Bundle
Identifier. Verify that it matches the actual project registration in Phase 3, from the list_projects tool call result.

Example checks:

    rg -n 'com\.com2usplatform\.hiveaxyl' Packages/manifest.json Packages/packages-lock.json
    rg -n 'Hive\.Axyl\.Core|Hive\.Axyl\.Core\.Unity|Hive\.Axyl\.Analytics' Assets -g '*.cs'
    rg -n 'CoreConfig\.CreateBuilder|\.Build\(' Assets -g '*.cs'
    rg -n 'HiveBootstrap\.Initialize\(|AddAnalytics\(' Assets -g '*.cs'

Axyl does not need v4's hive_config.xml, HiveActivity, HIVEAppDelegate, or AuthV4.setup.
Do not report v4 items as missing Axyl items.

Sending Analytics requires the Analytics module.

- Package: `com.com2usplatform.hiveaxyl.analytics`. It works with only the common module (core) and does not need the auth module.
- Registration: `builder.AddAnalytics()` in the assemble callback of `HiveBootstrap.Initialize`. Initialization happens only once per
  app run, so add only `AddAnalytics()` to the existing Initialize call. Do not call Initialize again.
- Usage: get it with `HiveCore.Resolve<IAnalyticsService>()` and call `CollectClientLogAsync()` (section 6).

A missing or unregistered Analytics module is not an integration gate failure. Report it as a prerequisite of code generation, and
after the user approves, add the manifest.json dependency and the `AddAnalytics()` registration.

Official documentation references:

- [Axyl SDK installation](https://developers.hiveplatform.ai/axyl/en/getting-started/2-sdk-installation/)
- [Axyl module installation](https://developers.hiveplatform.ai/axyl/en/getting-started/3-sdk-module-installation/)
- [Axyl SDK initialization](https://developers.hiveplatform.ai/axyl/en/getting-started/4-initialization/)
- [Creating an Axyl App ID](https://developers.hiveplatform.ai/axyl/en/getting-started/1-create-app-info/)
- [Axyl Analytics module installation and initialization](https://developers.hiveplatform.ai/axyl/en/analytics/init/)

## 2. Properties auto-collected when the Axyl SDK client sends

When an event is sent through the Axyl SDK's client features, the SDK and the gateway fill in the headers below, and the
receiving stage appends the header values to the logBody as JSON. Only headers whose value is not null are added.

| Send header | Value | Converted key | Ingestion location |
|-----------|-----|---------|-----------|
| X-App-Id | The appId from the SDK initialization configuration | `appId` | Top-level column |
| X-Hive-Player-Id | The Hive PlayerId the gateway parses from the auth token claim | `userId` | Top-level column |
| X-Hive-Device-Key | The DeviceKey the gateway parses from the auth token claim | `deviceId` | hiveAttributes |
| X-Hive-Aud | The Hive token audience `{appIndex}-{gameIndex}-{companyIndex}` | `aud` | hiveAttributes |
| X-Hive-Subject-Type | The Hive Subject type | `subjectType` | hiveAttributes |
| X-Hive-Client-Ip | The client IP | `clientIp` | hiveAttributes |
| X-Hive-Country-Code | The country code the gateway determines. `XX` when undeterminable | `country` | hiveAttributes |
| X-Platform | The client platform. android, ios, web | `os` | hiveAttributes |
| X-SDK-Version | The Axyl SDK version | `sdkVer` | hiveAttributes |
| X-OS-Version | The OS version | `osVer` | hiveAttributes |
| Accept-Language | The currently configured language. Reflected immediately on a runtime change | `lang` | hiveAttributes |
| User-Agent | `HiveAxyl/{SDK version} Unity/{engine version} {OS}/{OS version} {bundle ID}/{app version}` | `userAgent` | hiveAttributes |
| traceparent | A W3C Trace Context the SDK generates per request | `traceparent` | hiveAttributes |
| X-Client-Session-Id | A GUID generated per app execution process | `sessionId` | hiveAttributes |

Header values are stored as the header sent them, without a prefix. The pipeline adds `_`-prefixed properties such as
`_dataSource` and `_geoIpCountry` on top of these. For events the Axyl client sends directly, `_dataSource` is
`axyl_custom_sdk`. The pipeline also always generates the appId-based `_market` and `_os`, and `_clientIp`. For privacy, a
client IP is always stored with its last octet set to 0 (`xx.xx.xx.xx` → `xx.xx.xx.0`), even when clientIp is sent.

Do not build these headers yourself in the game code.

### Only appId and userId are satisfied by auto-collection

Two values are ingested as top-level columns: `appId` and `userId`. Every other header is ingested into hiveAttributes
without a prefix, as shown in the table above.

Some of those names are the same as the dimension names `list_dimensions` and `get_event_spec` return — `os`, `lang`,
`country`. When an event definition requires such a property, do not decide on your own. Ask the user whether to use the
value Axyl already collects in hiveAttributes, or have the game send its own value into eventAttributes. The hiveAttributes
value is the header value as it arrived (for example `os` is `android`, not the Hive code value `A`). If the user chooses to
send it, follow section 5 of `send_event_rule` for the value contract.

A name starting with `_` is reserved for properties the analytics pipeline processes. The game does not send a prefixed name
such as `_dataSource` or `_geoIpCountry` as a custom property.

### Difference in collection scope before and after login

Axyl splits the send path by auth state, and the headers the gateway fills differ.

| Path | When | Headers not collected |
|------|------|--------------------|
| Axyl RequestHeader | After login | None |
| AxylPublic RequestHeader | Before login | X-Hive-Device-Key, X-Hive-Player-Id, X-Hive-Aud, X-Hive-Subject-Type |

`appId`, `clientIp`, `country`, and the optional headers are still collected before login. Pre-login events are therefore
valid send targets. Follow section 3 for the detailed handling.

Consolidate the send calls in the repository's existing central wrapper. If there is no central wrapper, create a single adapter
matching the repository's conventions. Do not assume that v4's `Analytics.sendAnalyticsLog` is the Axyl API. The Axyl send API is
`IAnalyticsService.CollectClientLogAsync()`; follow section 6 for its call form and its return and error contracts.

## 3. Axyl collection ownership

Interpret the target_collect of the event and of each property separately.

| Definition result | Handling |
|-----------|------|
| Event AUTO | Excluded from ordinary recommendation and creation. Use the existing collection from the SDK or an Axyl module |
| Event GAME | A game send candidate |
| A GAME event's property is AUTO | Check the definition description and the required property policy |
| A GAME event's property is GAME | Find the value source in the game code and send it |

Current handling of Axyl's required properties:

| Property | Handling |
|------|------|
| userId | Auto-collected by the gateway from X-Hive-Player-Id. Do not set `ClientLogEvent.UserId` |
| deviceId | The game passes the app's DeviceKey directly in `ClientLogEvent.DeviceId`. Always sent, regardless of auth state |
| identifierProvider | The server always overwrites it with `hive`. Do not set `ClientLogEvent.IdentifierProvider` |
| appId | The SDK passes the CoreConfig initialization value automatically with every request (X-App-Id), and it is auto-collected at the receiving stage |
| eventTime | The game passes the event occurrence time directly in `ClientLogEvent.EventTime` as a `DateTimeOffset`. The SDK converts it to an RFC 3339 string including the UTC offset |
| eventName | The game passes the name from the event definition in `ClientLogEvent.EventName` |

There are three required properties the game puts in itself: deviceId, eventTime, and eventName.
userId, appId, and identifierProvider are filled by the SDK, the gateway, and the server, so the game does not set them.

### Handling a missing required property

If any required property is absent or empty, the entire log is quarantined into the rescue table. Even when a value
cannot be obtained, do not omit the property — fill it with `"0"` or `"unknown"` and send it.

- Fix eventName in the definition and design. If the event name is unknown, do not insert a fallback — do not create the send point.
- Put the actual event occurrence time in eventTime. It is always obtainable, so do not use a fallback.
  If `EventTime` is not set, the SDK raises no error and sends the `DateTimeOffset` default
  `0001-01-01T00:00:00.0000000+00:00` as is, so always set it. Even when events are collected and sent later, put in the
  occurrence time, not the send time.
- The server always overwrites identifierProvider with `hive`, so the game does not set it.
- Obtain deviceId through the DeviceKey rules below. Use `"0"` or `"unknown"` only when it cannot be obtained.
- This rule applies to required properties only. For event properties, do not insert an arbitrary fallback when the value
  is unknown — leave them with the value source unconnected. An empty event property is not a quarantine reason.

### userId auto-collection and pre-login events

The gateway parses userId from the auth token claim and collects it automatically. The game does not read the PlayerId
from the session and put it in the payload.

- Before login and after logout, the X-Hive-Player-Id header is not sent. userId for that window is filled with `"0"`
  at the receiving stage. Do not build a branch in the game that conditionally inserts userId based on login state.
- Pre-login events are valid send targets. Do not classify them as `not currently implementable` on the grounds that
  userId cannot be obtained.
- Send an event that genuinely needs userId, such as login success, only after token issuance and session setup are
  complete. If it is sent before `ISessionManager.SetSession` completes, userId is ingested as `"0"`.
- The session does not persist across app restarts, so re-establish it in the auto-login or the repository's auth restoration flow.
- Do not buffer pre-login events and retroactively send them with the userId obtained after login. Earlier anonymous
  behavior could be misattributed to the account that later logged in. Use deviceId to connect users in the pre-login window.
- Do not send a game-specific account ID as userId, and do not build userId by parsing an access token.
- On logout, session expiry, and account switching, confirm that the old session is not still in use.

### Rules for creating, storing, and reusing DeviceKey

deviceKey is not a hardware identifier the SDK looks up for you — it is a value the app creates and passes in the request.
Axyl requires deviceKey on every login request, whether guest, username, or an external auth provider, so the app always
holds this value. Use the same value for the Analytics deviceId.

Official value constraints:

| Item | Rule |
|------|------|
| Creation time | Generated exactly once, on the app's first run |
| Recommended format | UUID v4. Other schemes such as UUID, a hexadecimal string, or base64 are also allowed |
| Length | At least 22 and at most 64 characters |
| Characters | ASCII only, excluding whitespace and control characters. Hangul and emoji are not allowed |
| Storage | Keep it in secure storage and reuse it on every subsequent login request |

- Confirm where the repository creates, stores, and passes deviceKey in the request, whether in guest account creation and login or in another auth flow.
- If an app-managed existing deviceKey is confirmed, do not create a new value — use it for the Analytics deviceId as well.
- If a custom auth implementation owns deviceKey creation and there is no existing value, generate a UUID-based value
  equivalent to `Guid.NewGuid().ToString("N")` once and store it. At 32 hex characters it satisfies the length and character constraints.
- When logging in again with the same guest account, reuse the existing deviceKey along with the PlayerId and GuestToken.
- Use `com.com2usplatform.hiveaxyl.storage` or the repository's existing secure and persistent storage. Prefer the existing auth storage structure over inventing a new storage mechanism.
- Do not embed a fixed string in the app code. If every user shares the same value, sessions overwrite each other.
- Do not generate a new value per event or per session, or arbitrarily combine OS hardware identifiers.
- If the stored deviceKey is lost, the existing refresh token no longer matches, the session on that device becomes invalid, and
  the user must log in again with a new deviceKey. A guest account recovers the same PlayerId by guest login with the stored
  GuestPlayerId and GuestToken and a new deviceKey, but the device-level session history starts over. Do not assume this rule for
  how other account types recover. In every case, do not create a separate deviceKey for Analytics.
- If a Recipe or the auth module manages deviceKey internally and does not expose it, send `"0"` or `"unknown"` as
  deviceId until an exposure point is confirmed, and report it as `needs further review: confirm the DeviceKey exposure point`.
  Do not omit a required property and quarantine the whole log.

hiveAttributes' `deviceId` is the value the gateway collected from X-Hive-Device-Key, and the top-level `deviceId`
column is the value the game sent. After login both values are ingested together, which is normal — do not treat it as a
duplicate and remove one of them.

Official documentation references:

- [Axyl guest login](https://developers.hiveplatform.ai/axyl/en/getting-started/6-login/guest-login/6-1-guest-login/)
- [Axyl guest account creation and DeviceKey](https://developers.hiveplatform.ai/axyl/en/getting-started/5-account-creation/5-guest-account/#guest-account-device-key)
- [Activating an Axyl session](https://developers.hiveplatform.ai/axyl/en/getting-started/6-login/guest-login/6-3-set-session/)
- [Axyl auto-login](https://developers.hiveplatform.ai/axyl/en/auth/advanced/auto-login/)
- [Axyl login getting started — DeviceKey and Client ID rules](https://developers.hiveplatform.ai/axyl/en/login/getting-started/#devicekey)

### appId handling rules

The SDK sends the CoreConfig appId confirmed at the integration gate as the X-App-Id header, and the receiving stage collects it as
the required appId property. Do not duplicate appId or appIdGroup in the game's logBody. appIdGroup is generated by the pipeline
from appId. Do not work around an AppID that failed the gate with an unknown value, and verify in the sample send that X-App-Id
connects to the actually ingested appId.

## 4. Event recommendation differences

- An ordinary recommendation queries all GAME and AUTO event templates with the Phase 3 company_cd and sdk_type=axyl.
- Mark AUTO as `SDK automatic collection` and do not implement it directly.
- Present is_baseline=Y GAME events first. If there is no insertion point, mark it `needs further review: insertion point to be confirmed`.
- For is_baseline=N, make a specific recommendation only for events whose system and insertion evidence you confirmed in the repository.
- The `_dataSource` for AUTO enrichment option B's direct sends is `axyl_custom_sdk`.
- Propose unique custom events only for systems the event templates do not cover.

If there are many candidates, show the core events and the events with repository evidence first, and summarize the rest as counts
per category. Do not repeat unnecessary approval questions per category.

## 5. Property mapping

Map properties in this order.

1. The Axyl required properties the game sends directly (deviceId, eventTime, eventName)
2. The common context enrichment properties
3. The event properties confirmed from get_event_spec
4. Items whose value source is unconfirmed

### Implementation rules for common context enrichment properties

In Axyl, the following properties are enriched by default even when they are absent from the get_event_spec metadata.

| Property | Value source | When there is no value |
|------|---------|--------------|
| os | Map the platform runtime value to the Hive OS code value | Omit |
| market | Map the build's store target to the Hive market code value | Omit |
| serverId | The current server from the server selection result, the login response, or the active session | Omit |
| country | An ISO 3166-1 alpha-2 country code whose meaning is confirmed | Omit |

Axyl already collects `os` (from X-Platform) and `country` (from X-Hive-Country-Code) into hiveAttributes as the header sent
them. For these two, ask the user whether to use the hiveAttributes value or have the game send its own value into
eventAttributes, and enrich them only when the user chooses to send. The SDK does not collect `market`, but the pipeline
generates the appId-based `_market`; ask the user whether `_market` is enough or the game should send `market`. `serverId` is
not collected, so the game enriches it.

`appId` and `userId` are auto-collected as top-level columns, so do not enrich them. `lang`, `sdkVer`, `osVer`,
`userAgent`, `traceparent`, `sessionId`, `aud`, `subjectType`, and `clientIp` are also collected into hiveAttributes and are
not default enrichment targets; if get_event_spec requires one of them, ask the user in the same way. Put common values other than the four
properties above in the payload, under the corresponding dimension name, only when get_event_spec requires them.

If an Axyl event definition returns appId or userId as GAME, do not duplicate it with a direct send — report it
as `needs further review: metadata collection ownership to be confirmed`.

Do not recompute the common values in each event wrapper — read them from a single provider and merge them into the flat payload.
Do not put the same property name in twice, and if get_event_spec defines the same property, that definition's type and value
convention take precedence. Do not fill an optional property with an empty string, unknown, or an arbitrary constant.

For `country`, first confirm the meaning and source already used in the repository. If the game backend's login response, account
profile, or session context has an ISO country code, preserve that meaning. If no such value exists, you can read the country code
from the client OS's region setting, but that value is the device region the user configured — not the current connection country or
an IP-based country. In that case, define and use `country` consistently as the device's configured country.

Do not convert language (`Application.systemLanguage`) into a country. The hiveAttributes `country` the gateway collects and
the `_geoIpCountry` the pipeline generates are IP-based values — do not assume they can be queried from the client, and do not
treat either as the same value as a custom `country`.
If you cannot confirm the country code and its meaning in the repository, omit `country`.

serverId is the runtime value of the server the current user is connected to. Find the runtime value in the server selection result, the login response, or the session object. Do not invent candidate values.

If you cannot confirm an event property's value, leave it as a parameter or report it in Phase 6 as an unconnected value source.
Do not confuse an unobtainable DeviceKey with the handling of an unconfirmed ordinary event property.

## 6. Code generation

### Structure

    An existing or new central event logger
    ├─ context provider     the value sources for the required properties sent directly and the common values
    ├─ payload builder      assembles the required properties + guid + the selected event properties
    ├─ transport adapter    a single place that calls the confirmed Axyl SDK send
    └─ event wrapper        the per-event type and value contract

The names above are role examples. If the repository has a central wrapper, reuse its structure and names, and only when there is
none, create an adapter matching the repository's conventions.

Generation rules:

- HiveEventContext wraps the repository's existing configuration and auth storage objects. Do not create a new imaginary global
  configuration type such as HiveEventConfig.
- Read deviceId from the DeviceKey confirmed to be app-managed in the repository. Always include it regardless of auth state;
  if you cannot confirm an exposure point, put in `"0"` or `"unknown"` and report it as an item needing further review.
- Build log events as `ClientLogEvent` from `Hive.Axyl.Analytics`, put them in `ClientLogCollectRequest.LogBody`, and send them with
  `IAnalyticsService.CollectClientLogAsync()`. Several events can be batched into one request.
- `ClientLogEvent` fields: `EventTime` (`DateTimeOffset`, required), `EventName` (required), `DeviceId`, `UserId`,
  `IdentifierProvider`, and `AdditionalProperties` (`IDictionary<string, string>`).
- Do not set `UserId` or `IdentifierProvider`. The SDK passes appId automatically with every request, so do not put it in the request.
  Do not build a branch that conditionally inserts userId based on login state. Call it the same way before and after login; when a
  session is active, the SDK includes the auth token automatically.
- Put `DateTimeOffset.Now` at the moment the event occurs in `EventTime`. Do not format it into a string yourself.
- Put the event properties, guid, and common enrichment properties such as os, market, serverId, and country all in
  `AdditionalProperties`. The SDK records each property as a field at the same level as eventName, so the structure stays flat.
- Each `AdditionalProperties` value is **a string holding the JSON value itself**, not display text. The SDK does not validate the
  values and writes them into the request body as is, so a single invalid value turns the body into invalid JSON, including the
  other events in the same request.

  | Kind of value | Value in C# code | JSON sent |
  |---------------|------------------|-----------|
  | Number | `"42"` | `42` |
  | String | `"\"gold\""` | `"gold"` |
  | Boolean | `"true"` | `true` |
  | JSON null | `"null"` | `null` |

  Route string values through a single helper that serializes them as JSON strings with quotes and backslashes escaped. Keep numeric
  properties as numeric JSON, and do not build nested objects or arrays.
- Do not use `eventTime`, `eventName`, `deviceId`, `userId`, or `identifierProvider` as `AdditionalProperties` keys. A field with the
  same name could be sent twice.
- Do not create a property name starting with `_`. It is reserved for properties the analytics pipeline processes.
- Branch on the returned `AnalyticsCollectClientLogResult` as `Success`, `Failure`, or `UnknownOutcome`. Treat only `Success` as
  success, and treat `UnknownOutcome` as a failure and record its result code. Do not return true when you have not confirmed success.

Structure example:

    using System;
    using System.Collections.Generic;
    using System.Threading.Tasks;
    using Hive.Axyl.Analytics;
    using Hive.Axyl.Core;

    public static ClientLogEvent Build(
        string eventName,
        DateTimeOffset eventTime,   // captured where the event happened, not at send time
        string deviceId,
        string guid,
        IDictionary<string, string> eventAttributes)
    {
        if (string.IsNullOrEmpty(eventName) || string.IsNullOrEmpty(guid))
        {
            // never throw on the game path: record the skip in the repository's central send log, then skip this event
            // CentralSendLog.RecordSkipped(eventName, guid, "missing eventName or guid");   // placeholder: replace with the repository's own send-log call
            return null;   // callers drop null events before SendAsync
        }

        var properties = new Dictionary<string, string>(eventAttributes ?? new Dictionary<string, string>());
        properties["guid"] = JsonString(guid);   // serialize strings as JSON strings

        return new ClientLogEvent
        {
            EventTime = eventTime,            // event occurrence time
            EventName = eventName,
            DeviceId  = string.IsNullOrEmpty(deviceId) ? "unknown" : deviceId,
            AdditionalProperties = properties,
        };
    }

    public static async Task<bool> SendAsync(IReadOnlyList<ClientLogEvent> events)
    {
        IAnalyticsService analytics = HiveCore.Resolve<IAnalyticsService>();
        var result = await analytics.CollectClientLogAsync(new ClientLogCollectRequest { LogBody = events });

        switch (result)
        {
            case AnalyticsCollectClientLogResult.Success:
                return true;
            case AnalyticsCollectClientLogResult.Failure failure:
                // record failure.Problem's Code, ExternalCode, and Message in the central send log
                return false;
            case AnalyticsCollectClientLogResult.UnknownOutcome unknownOutcome:
                // record unknownOutcome.Code and RawJson and treat it as a failure
                return false;
            default:
                return false;
        }
    }

This example shows the structure of the required properties the game puts in itself and of the send result handling. The absence
of userId, appId, and identifierProvider is deliberate. Implement `JsonString` with the repository's existing JSON serialization; if
there is none, create one helper that follows the escaping rules. Connect deviceId to the actual value source confirmed in the
repository. The deviceId fallback exists to keep the whole log from being quarantined when the value could not be obtained; it does
not mean you may skip looking for the source. If the installed SDK version's types or signatures differ from the above, the
installed SDK takes precedence — report the difference. Do not invent a fake API.

Official documentation references:

- [Sending Axyl event logs](https://developers.hiveplatform.ai/axyl/en/analytics/send-log/)
- [IAnalyticsService](https://developers.hiveplatform.ai/axyl/en/api-reference/sdk-api-reference/analytics/analytics-service/)

## 7. Periodically sent events

Do not implement an event whose definition requires periodic sending, such as app_session_maintain, as a single inserted call.
Confirm the exact interval, the start and stop conditions, and the property names from the description and attributes in the
get_event_spec tool call result.

Implementation requirements:

- Start it on a successful login and stop it on logout or session expiry.
- Keep exactly one periodic execution routine per session.
- If existing heartbeat/keep-alive logic exists, reuse it but confirm that the defined interval matches.
- In Unity, use a wait that is unaffected by timeScale.
- Ensure the necessary state survives scene transitions.
- Accumulate the interval measurements since the previous send and reset them after sending.
- Measure the time entering and returning from background separately.
- Do not put 0 in for an unconfirmed interval value. 0 is aggregated as a valid measurement.

If you cannot find the login and logout points or the required measurements, do not add periodic execution logic at an arbitrary
location — report it as an unconfirmed item.

## 8. Code verification

- Perform the Unity compile or whatever static checks are possible.
- Confirm that the using/import statements and the types used exist in the actual project.
- Confirm that the 3 directly sent required properties (deviceId, eventTime, eventName) are in `ClientLogEvent` fields, and that
  guid and the event properties are placed flat in `AdditionalProperties`.
- Confirm that deviceId, eventTime, and eventName are neither missing nor empty. In particular, confirm that `EventTime` is set on
  every construction path so that the `0001-01-01` default is never sent.
- Confirm that `UserId` and `IdentifierProvider` are not set and that appId and appIdGroup are not put in the request.
- Confirm that every `AdditionalProperties` value is a valid JSON value string (strings quoted and escaped).
- Confirm that no `AdditionalProperties` key is `eventTime`, `eventName`, `deviceId`, `userId`, or `identifierProvider`.
- Confirm that the Analytics module (`com.com2usplatform.hiveaxyl.analytics`) is installed and that `AddAnalytics()` is registered
  exactly once in the existing Initialize call.
- Confirm that deviceId is always sent regardless of auth state, with no branch on login status.
- Confirm that DeviceKey satisfies the constraints: 22–64 characters, ASCII excluding whitespace and control characters.
- Confirm that auth and Analytics use the app-managed DeviceKey together and that it persists across app restarts.
- Confirm that DeviceKey was not embedded as a fixed string in the app code.
- Confirm that DeviceKey is not regenerated per event or per session.
- Confirm that the `"0"` or `"unknown"` fallback was used only when the DeviceKey exposure point could not be found, and that it
  was reported as an item needing further review.
- Confirm that guid is generated per event and that the same value is recorded in the central send log.
- Confirm that no queue was created that retroactively attributes pre-login events to a later PlayerId.
- Confirm that no property name starting with `_` was created in the game payload.
- Confirm that the user chose, for `os` and `country` (and any other same-name property get_event_spec requires), between the
  hiveAttributes value and a game-sent eventAttributes value, and that the code follows that choice. If the game sends `os`,
  confirm it is mapped to the Hive code value.
- Do not verify the auto-collected properties with an HTTP sample send. After running the actual game client, query `query_adhoc` by
  AppID and eventName over a narrow time range and confirm them in the actually ingested rows.
- In the ingested rows, confirm that the top-level `userId` and `appId` are filled and that the header values (`os`, `lang`, and so on)
  arrived in hiveAttributes. For pre-login sends, confirm that `userId` is `"0"`.
- Confirm that no common properties beyond os, market, serverId, and country were mixed into every event regardless of the event definition.
- Confirm that the common context enrichment properties' value sources and meanings are confirmed, and that unconfirmed values were omitted.
- Confirm that the periodic execution logic is not created twice and that the start and stop points are connected.
- Review whether the `CollectClientLogAsync()` result is branched into `Success`, `Failure`, and `UnknownOutcome` with only `Success`
  treated as success, and whether the types and signatures were confirmed from the installed SDK.
