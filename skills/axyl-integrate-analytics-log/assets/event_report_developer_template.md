# <Game Name> Analytics Event Development Specification

## Document Information

| Item | Content |
|------|------|
| Intended readers | Developers |
| Game | <game name> |
| SDK | <Hive SDK v4 or Hive Axyl> |
| Target AppIDs | <AppID list> |
| As-of date | <YYYY-MM-DD> |
| Implementation scope | <recommendation only / selected implementation / full implementation> |

## Event Status

Show every event template in the lists below. Record AUTO events in their dedicated list with only the event name, description, and
collection ownership. Record the design judgment and implementation status for GAME and custom events, and regroup the GAME events
you will not implement by reason under `Events not implemented and why`.

| Total event template candidates | SDK automatic collection | Total GAME | Implementable | Existing send confirmed | Not currently implementable | Needs further review |
|----------------|----------------|-----------|-----------|----------------|------------------|----------------|
| <count> | <count> | <count> | <count> | <count> | <count> | <count> |

Total event template candidates = `SDK automatic collection + total GAME`, and total GAME must equal the sum of the four statuses
that follow. When AUTO enrichment was reviewed, show the original `SDK automatic collection` status together with `AUTO enrichment exception`.

### SDK auto-collected events

| eventName | Description | Collection ownership |
|-----------|------|-----------|
| `<event_name>` | <description_ko> | SDK automatic collection |

### GAME and custom events

| eventName | Kind | Category | Description | Trigger | Design judgment | Implementation status |
|-----------|------|----------|------|--------|-----------|-----------|
| `<event_name>` | <event template / company-specific custom / repository-unique custom> | <category> | <description_ko> | <occurrence condition> | <implementable / existing send confirmed / not currently implementable / needs further review> | <not implemented / implemented / no additional implementation / deferred> |

## Common Send Rules

- payload structure: flat JSON
- Required properties sent directly by the SDK integration: <required properties per SDK>
- Runtime diagnostics: trace the SDK call and actual ingestion by `eventName` and `guid`
- Expected `_dataSource`: <custom_sdk or axyl_custom_sdk>

### SDK auto-collected properties

| Property | SDK value source | Included in the game payload | Verification status |
|------|-------------|------------------------|-----------|
| `<attribute>` | <SDK configuration, header, session, and so on> | Excluded | <confirmed / unconfirmed> |

Axyl records the top-level columns `appId` and `userId`, plus `deviceId`, `aud`, `subjectType`, `clientIp`, `country`,
`os`, `sdkVer`, `osVer`, `lang`, `userAgent`, `traceparent`, and `sessionId` in hiveAttributes, as the headers sent them. The
pipeline adds `_dataSource`, `_geoIpCountry`, `_clientIp` (last octet masked to 0), `_market`, and `_os` on top. When the definition requires `os`, `lang`, or `country`, record which
the user chose: the hiveAttributes value, or a direct send from the game into eventAttributes.
For v4, write this based on the
auto-collected properties in the [SDK v4 flow](../references/flow_sdk_v4.md). Do not duplicate auto-collected properties in the event
payload examples.

## Event Details

Write these only for GAME, company-specific custom, repository-unique custom, and AUTO enrichment exceptions. For an ordinary AUTO
event, record only the eventName, description, and `AUTO` collection ownership in the status list above — do not write detailed
properties, example values, or a payload.

### `<event_name>`

| Item | Content |
|------|------|
| Kind | <event template / company-specific custom / repository-unique custom> |
| Category | <category> |
| Description | <description_ko, or a description based on repository evidence> |
| Collection ownership | <GAME / AUTO / AUTO enrichment exception> |
| Baseline event | <whether it is baseline> |
| Trigger | <the exact occurrence condition and send timing> |
| Insertion point | `<repo-relative-path>:<line> - <function>` |
| Design judgment | <SDK automatic collection / implementable / existing send confirmed / not currently implementable / needs further review> |
| Implementation status | <automatically collected / not implemented / implemented / no additional implementation / deferred> |

#### Properties

| Property | Data type | Collection ownership | Description and value convention | Example value | Value source | Implementation status |
|------|--------|-----------|--------------|---------|---------|-----------|
| `<attribute>` | <INT / STRING / TIMESTAMP> | <GAME / AUTO> | <desc_ko> | `<example>` | `<path>:<line> - <variable/function>` | <connected / unconnected / not applicable> |

#### Payload example

Write this only for GAME or an AUTO enrichment exception. Mark an ordinary AUTO event as SDK automatic collection and do not build a
game payload.

```json
{
  "eventName": "<event_name>",
  "guid": "<uuid>",
  "<attribute>": "<example>"
}
```

#### Duplicate and ingestion check

| AppID | Existing code | Recent ingestion | Judgment |
|-------|-----------|-----------|------|
| `<app_id>` | <present / absent / unconfirmed> | <present / absent / query failed> | <new / duplicate / partially collected / unconfirmed> |

#### Runtime check

- Send attempt log: `[HiveAnalytics] send_attempt eventName=<event_name> guid=<guid>`
- SDK result log: <the log to check, or the SDK result contract>
- Actual ingestion check: query by AppID, eventName, and time, then match `eventAttributes.guid`

#### Items needing further review

- <value sources, SDK APIs, call timing, or items to check after the build>

## Events Not Implemented and Why

Group them by reason and record every event in each group, with none omitted. Classify anything you could not confirm in the code as
`needs further review`, and do not conclude that a system or flow does not exist.

The reason categories to use are: `existing send code confirmed`, `recent actual ingestion confirmed`, `no target system`, `no event
occurrence flow`, `no available send point`, `cannot obtain a required value`, `SDK constraint`, `a policy or scope decision is
needed`, `duplication risk on some AppIDs`, `system, flow, insertion point, value source, or SDK API to be confirmed`, and
`deferred out of this scope at the user's request`.

### <reason category> — <count>

| eventName | Status | Specific reason | Evidence |
|-----------|------|-----------|------|
| `<event_name>` | <existing send confirmed / not currently implementable / needs further review> | <the specific reason this event is not implemented> | <the query result or code location> |

## Verification Results

| Verification item | Result | Evidence and how it was checked |
|-----------|------|----------------|
| Static checks and compilation | <passed / failed / not performed> | <the command, or why it was not performed> |
| SDK call diagnostics | <implemented / not implemented> | <the log location and how to check it> |
| Sample metric contamination prevention | <already protected / metric exclusion registered / CSV created for an administrator request / metric start date registered / administrator request / no configuration change> | <the target project and the check result, or the remaining risk> |
| Sample send | <succeeded / quarantined / delayed / not performed> | <the guid, or why it was not performed> |
| Actual game build | <performed / not performed> | <the result, or how to check it on the built client> |

## Remaining Items to Confirm

- <items that development or QA must confirm or decide>
