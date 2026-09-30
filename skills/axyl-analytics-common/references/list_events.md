# list_events (List Events)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To confirm the `event_idx`/`event_name` to use for `preview_chart` in event mode, `preview_funnel`'s `sections`, and `preview_retention`'s `base_event`/`retention_event`.
- When the metric you want is not registered in `list_metrics` (SCHEMA_FIRST — enter this path only when the metric is unregistered).
- If an event name has already been confirmed in the same conversation, do not call this again.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |

## Return Value

For each event, returns the company-specific `event_idx`, the name and description, and the
company-level most recent ingestion time `last_data_date_kst`.

- `event_idx`: use for `preview_chart`'s `event_measures[].event_idx`, `preview_funnel`'s `sections[].event_idx`, and `preview_retention`'s `base_event.idx`/`retention_event.idx`.
- `event_description`: the Korean description from the event metadata. It is `null` for unregistered events and may simply repeat the event name, so use it only as supporting information when asking the user to choose an event.
- `last_data_date_kst`: the time (KST) this event was last ingested. This is the primary evidence for whether the event is actually being collected.
  **It is a company-level value, so it says nothing about collection per project (`appid_group`).** In dashboard readiness checks, treat
  `null` or a value older than 14 days as `NOT_READY / NO_RECENT_DATA` and stop checking that event's project and property
  ingestion. If it is within the last 14 days, check the property definitions with `list_dimensions` and the project-level values with `query_adhoc`.

## Decision Rules

- Do not guess or invent `event_idx`/`event_name`.
- If a required event is not in the list, judge it `NOT_READY / EVENT_NOT_DEFINED`. Events register automatically
  on their first log, so this means the log has never arrived — the fix is log integration, not `regist_event`.
- If `last_data_date_kst` is `null` or older than 14 days, judge it `NOT_READY / NO_RECENT_DATA` and skip property and raw
  ingestion queries. This does not confirm that the log was never implemented, nor does it exclude the content from recommendations.
- If the event name is ambiguous or there are several candidates, show the list and ask the user to choose.
- Query dimension (property) details separately with `list_dimensions(company_cd, event_name)`, not with this tool.

## On Failure

- Empty result: check that `company_cd` is correct.
- The event you want is not in the list: perform FUZZY_SEARCH_FALLBACK — broaden the keywords and search again; if it is still missing, present the full list.

## Recommended Chain

```
list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart / preview_chart_rank / preview_funnel / preview_retention
```
