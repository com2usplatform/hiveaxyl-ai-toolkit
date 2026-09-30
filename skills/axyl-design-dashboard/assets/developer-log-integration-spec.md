# <Game Name> Dashboard Log Integration Requirements

## Document Information

| Item | Content |
|---|---|
| Target project | <the project name / appid_group confirmed through PROJECT_ID_GATE> |
| Target AppIDs | <the list of confirmed AppIDs> |
| Requested dashboard | <dashboard name> |
| Intended readers | Game client and server developers / data owners |
| As-of date | <YYYY-MM-DD, KST> |
| Document status | <draft / confirmed by the user / reviewed by development> |

## Background of the Request

- Dashboard purpose: <the question this dashboard is meant to answer>
- Currently implementable scope: <the content that can be built right away>
- Scope needing log improvements: <the content that cannot be built now or is expected to be empty>

## Current Findings

| Content | Required event / property | Metadata definition | Recently collected | Current limitation |
|---|---|---|---|---|
| <content name> | `<event_name>` / `<attribute>` | <existing definition / undefined / to be confirmed> | <has values / all null / no rows / unverifiable> | <the impact on aggregation, breakdown, and filtering> |

`No rows` does not by itself mean it was never implemented. Record the queried project and period along with the raw log check results as evidence.

## Integration Requirements

### `<event_name>` — <existing definition | proposed>

| Item | Requirement |
|---|---|
| Business meaning | <the user behavior or state this event represents> |
| Trigger condition | <the exact trigger, or to be confirmed> |
| Send timing | <after successful completion / on entry / on state change / to be confirmed> |
| Sender | <game client / game server / SDK automatic / to be confirmed> |
| Duplication rule | <one record per occurrence of the behavior, and so on, or to be confirmed> |
| Target AppIDs | <all / a list of some AppIDs> |
| Content using it | <the dashboard content that uses this event> |

#### Properties

| Property name | Kind | Data type | Required / nullable | Meaning and value convention | Example value | How the dashboard uses it |
|---|---|---|---|---|---|---|
| `<attribute>` | <existing definition / proposed> | <STRING / INT / TIMESTAMP / to be confirmed> | <required / optional / to be confirmed> | <allowed values, units, null conditions> | `<example>` | <aggregation / breakdown / filter / funnel condition> |

#### Example payload

Write this only when the SDK and the send format have been confirmed. Do not duplicate automatically collected fields in the game payload.

```json
{
  "eventName": "<event_name>",
  "<attribute>": "<example>"
}
```

## Completion Criteria

| Verification item | Completion criterion | How to verify |
|---|---|---|
| Event definition | Defined in the agreed event specification; it appears in the company metadata once its first log arrives (events register automatically) | Check the official specification, then `list_events` after the first send |
| Property definition | The name, data type, collection ownership, and value convention are settled | Check `list_dimensions` or the official specification |
| Actual sending | The event is collected once per agreed trigger on the target AppIDs | Run a test and check the SDK response |
| Actual ingestion | Raw rows and non-null values are confirmed for the properties strictly required to compute, break down, or filter this content | `query_adhoc` |
| Content display | The expected metric and breakdown results appear in the preview | Run the corresponding `preview_*` |

## Items Needing Confirmation from Development

- <the event's trigger point, or client versus server ownership>
- <the actual source of the property value in the code>
- <the duplication, retry, and offline sending policy>
- <review of personal, payment, and in-game currency information>
- <whether it applies to only some AppIDs>

## Dashboard Rollout Plan

| Content | Before the log is ready | After the log is ready |
|---|---|---|
| <content name> | <create empty content / defer creation / create with limited features> | <re-verify with preview, then create or replace> |
