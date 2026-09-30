# query_adhoc (Query Raw Event Logs Directly)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To confirm from the original rows whether a specific event **was actually ingested**.
- For ingestion verification after `run_etl_simulation` (axyl-integrate-analytics-log Phase 7).
- To rule out duplicate sends by judging whether an event is already being sent (Phase 4). Include the confirmed `appId` in the filters.
- To confirm that property values are actually being ingested, or which code values are already in use (such as `GO`/`AP` in
  `market`), across a whole period rather than a sample — pass `dimension_names`.
- If the goal is a metric aggregation or charting, use `preview_chart` instead. This tool is for inspecting raw events.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | The company code confirmed through PROJECT_ID_GATE |
| `org_idx` | Y | Organization idx. Verifies access to all of the `appid_groups` below |
| `appid_groups` | Y | The list of project IDs confirmed with `list_projects`. 1–50 entries |
| `event_name` | Y* | The event name confirmed from `list_events`. *Can be omitted only with `dimension_names` — then every event of the project is aggregated |
| `start_date` | Y | The KST start date to query, `YYYY-MM-DD` |
| `end_date` | Y | Same format as `start_date`. Includes that entire KST end date |
| `filters` | N | Equality filters on the allowed top-level columns. Up to 5 |
| `limit` | N | Maximum rows returned for an ordinary query. 1–100, default `10` |
| `app_ids` | N | A string array for checking collection across several AppIDs at once. 1–50 entries |
| `dimension_names` | N | Property names from `list_dimensions` to aggregate. 1–20 entries. Switches the return value to a per-property value distribution |
| `value_limit` | N | With `dimension_names`, how many values to return per property, most frequent first. 1–100, default `20` |

Because the end date is included, the difference between the `start_date` and `end_date` inputs is at most 30 days and the
actual query range is at most 31 days. The allowed filters are `identifierProvider`, `userId`, `deviceId`, `appId`, and
`appIdGroup`, and no value may exceed 512 characters.

When `app_ids` is specified, the tool returns one most-recent row per AppID by `dateTime` and `limit` does not apply.
`filters.appId` and `app_ids` cannot be specified together.

When `dimension_names` is specified, the tool aggregates every row in the period instead of returning rows, and `limit` does not
apply. `app_ids` then works only as an AppID filter, not as the latest-row-per-AppID mode. The BigQuery scan is the same as an
ordinary query. Top-level column names (`identifierProvider`, `userId`, `deviceId`, `appId`, `appIdGroup`) are read from the column;
every other name is looked up under both `hiveAttributes` and `eventAttributes`. Names must consist of letters, digits, and underscores.

With `dimension_names`, `event_name` can be omitted to aggregate every event of the project. Use this broad mode for discovery,
not as final evidence for a code system: query `_dataSource`, identify event names under the target SDK's direct-send value
(`custom_sdk` for SDK v4, `axyl_custom_sdk` for Hive Axyl), and then query the relevant dimensions again with one of those
customer SDK event names. Without the event filter the scan grows sharply, so the range is then limited to at most 14 days
including the end date.

## Return Value

Returns a list of raw event rows, or an empty list when there are no results. Each row includes the common identifier,
project, event, and time fields, plus `hiveAttributes` and `eventAttributes`.

- The 7 top-level columns come back as is, and `attributes` is returned split into the two objects `hiveAttributes` and `eventAttributes`.
- `dateTime` is UTC. Convert it to KST when reporting to the user.
- Values added by the collection system can also appear in the event properties, so read them as distinct from the properties the game sent.

With `dimension_names`, it returns `{"event_rows", "dimensions", "missing_dimensions"}` instead.

- `event_rows`: the number of event rows matching the conditions.
- `dimensions[]`: one entry per source where the property had at least one non-null value — `attribute_source`
  (`"top"`, `"hiveAttributes"`, or `"eventAttributes"`), `dimension_name`, `non_null_count`, `null_count`, `value_variety`
  (distinct non-null values), `values` (`[{"value", "count"}]`, most frequent first, up to `value_limit`; with `event_name`
  omitted, each value also carries `events`, up to 10 event names it appeared in), and `values_truncated`.
- `missing_dimensions`: names that were null or absent in every source.
- Values come back as strings, numbers included. Empty strings, objects, and arrays count as null.

## Decision Rules

- **Use only the allowed top-level columns in `filters`.** Do not pass event properties or storage-path expressions as filters —
  check them in the returned result instead.
  - A dimension whose `list_dimensions` `attribute_source` is `null` → a top-level column, so it can be used in `filters`.
  - A dimension whose `attribute_source` is `"hiveAttributes"` / `"eventAttributes"` → do not put it in `filters`. Read the value from the returned `attributes`.
- All `filters` values are compared as strings. Pass them as strings even for numeric columns.
- For a single AppID use `filters={"appId":"..."}`; for several use `app_ids=[...]`. Do not call once per AppID, and do not
  invent array or IN-operator structures inside `filters`. The one exception: `dimension_names` mode merges the AppIDs in
  `app_ids` into one distribution, so when a per-AppID value distribution is needed, call once per AppID with `filters.appId`.
- If a requested AppID is absent from the `app_ids` result, judge that AppID as having unconfirmed collection within the query period.
- With `dimension_names`, `event_rows > 0` and a name in `missing_dimensions` means the event arrives but that property is empty.
  `event_rows = 0` means the event itself was not found in the period.
- With `dimension_names`, judge the entry whose `attribute_source` matches `list_dimensions` (`null` there is `"top"` here).
  The same name can exist in both `hiveAttributes` and `eventAttributes` with different values. Where a value lives depends on
  the SDK:

  | | SDK v4 | Hive Axyl |
  |---|---|---|
  | SDK auto-collected (`os`, `market`, and so on) | eventAttributes | hiveAttributes (header values as sent, no `market`) |
  | Game custom properties | eventAttributes | eventAttributes |
  | Pipeline-processed, from appId (`_market`, `_os`) | hiveAttributes | hiveAttributes |

  Only pipeline-processed properties carry the `_` prefix. The table covers logs the customer sends through the SDK; Hive
  platform logs (such as `_dataSource = hive_server`) can differ.
- For high-cardinality properties such as `userId`, `values` holds only the top entries — use `non_null_count` and
  `value_variety`, not `values`, as the collection evidence.
- When `event_name` is omitted, each value's `events` contains at most 10 event names. It is a discovery aid, not a complete
  event inventory. For code-value confirmation, choose an event listed under the exact `_dataSource` value for the target SDK
  and rerun the query with that `event_name`.
- Enter dates in KST and apply no additional time zone correction.
- `event_name` and the date range are required; do not omit them or widen them to the full range. The only exception is
  omitting `event_name` in `dimension_names` mode (at most 14 days).
- You cannot query another company's dataset or a project the organization cannot access. Do not try to work around this by
  combining unverified `company_cd`, `org_idx`, or `appid_groups` values.

## On Failure

- **Do not conclude from an empty result that the send failed.** Distinguish three cases.
  1. Whether the send response itself was a failure
  2. Quarantine — a format error kept it out of the normal store. The quarantine criteria follow the quarantine items defined in the
     SDK log send rules of the `axyl-integrate-analytics-log` skill
  3. Ingestion lag — it goes through ETL, so it may not be there yet right after sending
- `Unrecognized name` error: an `attributes` sub-property name was put in `filters`. Switch to a top-level column, or query without the filter and check the result.
- If there is still no result, report the state after the retry limit as it stands. Do not assume it was ingested.

## Recommended Chain

```
[Ingestion check] run_etl_simulation(org_idx, dry_run=false, confirmation_token=<value returned by the dry-run>)
                  → query_adhoc → (if absent) check quarantine
[Rule out dupes]  list_projects (confirm project and AppID) → query_adhoc(org_idx, appid_groups, app_ids=[...]) → event recommendation
[Check property]  list_dimensions (check attribute_source) → query_adhoc(dimension_names=[...]) → value distribution
[Code values]     query_adhoc(event_name omitted, last 14 days, dimension_names=["_dataSource"])
                  → select an event under custom_sdk (v4) or axyl_custom_sdk (Axyl)
                  → query_adhoc(event_name=<selected event>, dimension_names=["market", "os", "_market", "_os"])
                  → read each entry by SDK (see the table above); use _market/_os only as a reference
```
