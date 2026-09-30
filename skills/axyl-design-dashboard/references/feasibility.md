# Content Data Readiness Judgment

Read this document when matching a selected candidate's metric, event, and property definitions against actual ingestion results.

## Extracting the Requirements

Organize each content item into the following structure.

```text
content_name
content_type / chart_type
purpose
preferred_metric
fallback_events[]
required_dimensions[]
optional_dimensions[]
filters / date_basis / currency_basis
mapping_confidence: confirmed | candidate | unmapped
source: recommended_catalog | platform_template | user_specified
```

- A platform dashboard template's `contents[]` holds child content references and layout information. When `cell_type=content`
  and a `content_idx` is present, do not judge it deleted, dataless, or unimplementable even if the parent response's
  `content_name`, `content_type`, and `chart_type` are `null`. Query that `content_idx` directly with `get_content_template`,
  and use the directly queried name, type, and `params` as the judgment basis. Only when the direct query also fails, record it
  as `child template details unavailable`.
- When a platform content template exists, base the judgment on `get_content_template.params`. **The tool already gives you the
  params' idx values substituted to the target company's values**. Do not look the company
  metric up again by name.
- An item listed in `params.unresolved_idx` is undefined at this company. Do not substitute a similar metric — leave it `unmapped`.
  Two kinds arrive mixed together — unmatched metric, event, and dimension idx values (`kind` of `metric`/`event`/`dimension`),
  and the absence of a dimension that exists by name only (`kind: "dimension_name"`; a funnel `identifier`, a retention `conditions`).
  The latter is also marked in place as `{key}_unresolved`.
- Split the ingestion-check evidence by measure type. A metric-based measure has no internal aggregation event or property in the
  template params, so obtain them from the company metric's `metric_config` per rule 4.
  An event-based measure uses the `{type:"event"}` / `{type:"event_detail"}` tokens from the template params directly.
- A user-specified composition keeps the metrics and conditions the user stated.
- Keep a recommended content item even when the recommendation catalog offers only a name, description, and importance. Extract the
  analysis intent from those values and look for implementation candidates in this order: the company metric's name, description,
  and formula → the event's name and description → the dimension definitions and recent collection.
  Adopt only items with explicit matching evidence. If there are several candidates, have the user choose; if there are none, leave it as
  `data contract unsettled` or `undefined`.
- Distinguish required from optional properties. Do not make a whole content item unimplementable over a missing optional property alone.

## Mapping Confidence

| Grade | Criterion | Handling |
|---|---|---|
| `confirmed` | **For an item from a template, the idx the tool already substituted is itself the confirming evidence** (the value the tool matched 1:1). Otherwise, the target company metric's purpose and formula match, or the event's name, description, and required dimensions uniquely match the analysis intent | Proceed with the readiness judgment |
| `candidate` | Two or more metrics or events could plausibly correspond by description, or only some conditions match | Show the candidates and their differences and wait for the user to choose |
| `unmapped` | There is no company metric or event that can be safely matched. A template item listed in `params.unresolved_idx` falls here | Do not map arbitrarily; propose a definition or a log design |

`importance` is evidence for content recommendation priority, not for data mapping. Do not automatically promote a
`candidate` to `confirmed`.

## Judgment Statuses

| Status | Reason code | Criterion | Explanation to the user |
|---|---|---|---|
| `READY` | `PREVIEW_OK` | A company metric preview result was handed over from an earlier step (this skill itself does not preview before DESIGN_APPROVAL_GATE) | Can be built with the current data |
| `READY` | `DIMENSION_SUBSTITUTED` | A required property `X` had no values in its source, and the user approved switching it to another source of the same property that has values (such as `_os` or `hiveAttributes.os`) | Can be built with the current data using the approved replacement dimension and filter-value mappings |
| `READY` | `RAW_DATA_CONFIRMED` | In event mode, the property metadata and `dimension_idx` exist and non-null values were confirmed in the `query_adhoc` raw rows for every property strictly required to compute, break down, or filter this content | Can be built with the current data |
| `PARTIAL_READY` | `OPTIONAL_DATA_MISSING` | The core metric is available, but optional breakdown or filter properties are missing or confirmed for only some AppIDs | The core composition is possible, with some features limited |
| `UNVERIFIED` | `METRIC_NOT_PREVIEWED` | The company metric exists but no preview has been run yet | The actual result must be confirmed at the creation stage |
| `UNVERIFIED` | `FILTER_VALUE_UNVERIFIED` | A replacement dimension has values, but a required filter value cannot be mapped to its value system from the available, possibly truncated distribution | The replacement is plausible, but its filter value must be confirmed before creation |
| `NOT_READY` | `EVENT_NOT_DEFINED` | The required event is not in `list_events` | No log for this event has arrived yet — events register automatically on their first log, so the log needs to be implemented |
| `NOT_READY` | `ATTRIBUTE_NOT_DEFINED` | A property strictly required to compute, break down, or filter this content is not in `list_dimensions` | Property metadata must be defined. Raw values alone cannot be used directly |
| `NOT_READY` | `NO_RECENT_DATA` | The event exists but `last_data_date_kst` is null or older than 14 days | No recent company-level ingestion. This does not confirm that the log was never implemented |
| `NOT_READY` | `ATTRIBUTE_NO_DATA` | Raw event rows exist but the properties strictly required to compute, break down, or filter this content have no values | The event arrives, but the values needed for computation, breakdown, or filtering are absent |
| `NOT_READY` | `NO_DATA` | `query_adhoc` finds no raw event rows for that project | No source data for the project in the query period |
| `UNMAPPED` | `DATA_CONTRACT_UNCONFIRMED` | There is no basis for safely mapping the recommended content to an actual metric or event | The required data definitions must be confirmed |
| `UNVERIFIABLE` | `QUERY_FAILED` | It cannot be judged due to a permission, tool, or query error, or a truncated result | The error must be resolved and the check rerun |

## Final Data Determination Rules, Event and Property Based

Do not skip or reorder the steps below.

```text
1. list_events — company event metadata and recent ingestion
   ├─ no event                 → NOT_READY / EVENT_NOT_DEFINED
   ├─ fixed-period metric      → use that period and continue to 2; do not apply the recent-14-day gate
   ├─ last_data_date_kst absent or over 14 days
   │                           → NOT_READY / NO_RECENT_DATA
   └─ within the last 14 days  → 2

2. list_dimensions — the property metadata needed for the content's computation
   ├─ required property metadata absent → NOT_READY / ATTRIBUTE_NOT_DEFINED
   └─ required property metadata present → 3

3. query_adhoc(dimension_names=[required properties]) — value distribution of the project's raw events
   ├─ every required property has a non-null entry in the attribute_source named by list_dimensions
   │                           → READY / RAW_DATA_CONFIRMED
   ├─ event_rows > 0, but a required property has no non-null entry in that source
   │                           → NOT_READY / ATTRIBUTE_NO_DATA
   ├─ event_rows = 0           → NOT_READY / NO_DATA
   └─ permission, tool, or query error → UNVERIFIABLE / QUERY_FAILED
```

Property metadata and raw values do not substitute for each other. Only a property that is defined in `list_dimensions` and has a
secured `dimension_idx` can be used in a content configuration. `query_adhoc` is the step that confirms whether that property's
actual values are being collected. Without property metadata it is `ATTRIBUTE_NOT_DEFINED` even when raw values exist, and
only when the property metadata exists can a raw-value check yield `RAW_DATA_CONFIRMED`.
An event-based measure does not support `COUNT(*)`, so always confirm at least one property to compute over.

## Detailed Judgment Rules

1. When a company metric exists, prefer it over event mode. However, the purpose and formula must match, not just the name.
2. The strongest evidence of `implementable` is a successful `preview_<type>` for that metric. If no preview was run at the
   recommendation stage, leave it as `metric registered, unverified`. Hand the preview verification to `axyl-create-content` only
   after the user approves the final composition.
3. In event mode, record the event definition, the definitions of the properties strictly required to compute, break down, or filter
   this content, and the recent ingestion, separately.
4. Decide the ingestion-check event and field per measure type.
   - Metric-based: the template params contain only the metric token, not the internal aggregation event and property. Use
     `list_metrics.metric_config` for the same `metric_idx`. Inside it, `{type:"event"}.text` is the event name and
     `{type:"event_detail"}.measure_field` is the property to check
     (for example, `인앱 매출액` / In-App Revenue → `product_purchase` / `totalPrice`).
   - Event-based: use `{type:"event"}.text` and `{type:"event_detail"}.measure_field` from the template params directly.
   The metric information was already fetched in Step 4-1, so make no extra call. Do not work backwards from an incoming property
   to the event, and when several measures converge on the same event, group them and check once.
5. Two-stage aggregation and per-term period metrics extract the event and property the same way as in rule 4. Note two things, however.
   - Even when `measure_formular` is comma-joined (`"COUNT_DISTINCT,MAX"`), the property to check is `measure_field` as is.
     `measure_group_field` (always `dateTime`) is **not an ingestion-check target** — it is a time column, so keep it out of the check list.
   - When `expressions[].measure_date` is a fixed (`"F"`) period, what matters is **ingestion in that period**, not recent ingestion.
     Do not attach `NO_RECENT_DATA` on a last-14-days basis; record it along with the fact that the metric references a fixed period.

6. `list_events.last_data_date_kst` is the company-level recent-ingestion gate.
   - If the required event is not in the list, judge it `NOT_READY / EVENT_NOT_DEFINED`.
   - For a fixed-period metric, do not apply this recent-ingestion gate. Continue with `list_dimensions` and query the fixed
     period, splitting it into consecutive windows of at most 31 days when necessary.
   - If the value is null or older than 14 days, judge it `NOT_READY / NO_RECENT_DATA` and skip the
     `list_dimensions` and `query_adhoc` queries for that event.
   - If the value is within the last 14 days, continue with the per-project readiness check. This signal alone does not make it `READY`.

   `NO_RECENT_DATA` is a current readiness judgment, not confirmation that the event was never implemented or that collection has
   permanently stopped. Do not remove the item from the recommendation catalog either — show only the readiness and the reason.

7. For every event that passed rule 6, call `query_adhoc` with the required properties in `dimension_names`. Only properties
   defined in `list_dimensions` are subject to judgment. Property metadata says only that the key is registered for this
   company; it does not prove that the project is sending values now, so always confirm the values in the raw events.
8. Separate the result into event rows and property values.
   - Every property strictly required to compute, break down, or filter this content is in `dimensions` →
     `READY / RAW_DATA_CONFIRMED`
   - `event_rows > 0`, but a required property has no entry in the source `list_dimensions` names (it is in
     `missing_dimensions`, or only another source has values) → `NOT_READY / ATTRIBUTE_NO_DATA`
     - For `os` and `market`, check the other sources in the same result in this order, and recommend the first one with
       values:
       1. `eventAttributes.X` — the value the customer sent (usually the required source itself)
       2. `hiveAttributes._X` — generated by the pipeline from appId
       3. `hiveAttributes.X` — collected by the Hive platform (for example, Axyl headers)
       Do not decide on your own. In the Phase 5 result review, tell the user the content will come out empty with `X`, show
       the values of each candidate, and let the user choose. A candidate can be offered only if `list_dimensions` defines it
       as its own dimension (its own `dimension_idx`).
     - The candidates follow different value systems: `_X` is derived from appId, not from what the build sends, and
       `hiveAttributes.os` is a header value such as `android`. Move filters together with the dimension; leaving a filter on
       the old, empty dimension would keep the content empty. For every filter value, determine the corresponding value in the
       chosen candidate's value system and record that mapping. Reuse the literal only when the same value is confirmed there.
       Never silently drop a filter.
     - Absence from `values` proves absence only when `values_truncated=false`. When it is `true`, retry with a larger
       `value_limit` (up to 100); if the result is still truncated or the mapping remains unclear, mark the filter value
       `unverified` and ask the user rather than concluding that it is absent.
     - Approved, with every required filter value mapped → `READY / DIMENSION_SUBSTITUTED`. Record
       `X → <chosen source>`, its `dimension_idx`, the affected slots, and the filter-value mappings in the handoff context.
       Declined → keep `NOT_READY / ATTRIBUTE_NO_DATA`. A required filter mapping left unconfirmed →
       `UNVERIFIED / FILTER_VALUE_UNVERIFIED`.
   - `event_rows = 0` → `NOT_READY / NO_DATA`
   - Permission, tool, or query error → `UNVERIFIABLE / QUERY_FAILED`
9. Keep `query_adhoc` to one call per event, and put every required property of that event in one `dimension_names` (up to 20).
   The cost is independent of how many properties you pass. The result aggregates every row in the period, not a sample, so a
   property in `missing_dimensions` had no non-null value anywhere in that period.
   Match `attribute_source` against `list_dimensions`: `null` there appears as `"top"` here, and a name can exist in both
   `hiveAttributes` and `eventAttributes` — judge only the entry in the source `list_dimensions` names. For a fixed-period metric,
   use that period instead of the last 14 days (at most 31 days per call; split longer periods into consecutive windows).
   Every event is stored in the raw log `query_adhoc` reads, so `event_rows = 0` means this project has no logs for it (`NO_DATA`).
10. For a multi-AppID project, distinguish fully ready from ready on some AppIDs. When a per-AppID check is needed, use
   `query_adhoc(org_idx=..., appid_groups=[...], app_ids=...)`. Because only the latest row per AppID comes back, use it solely as
   evidence of whether the event is collected — do not judge the presence of property values from that one row. To check property
   values for one AppID, call `dimension_names` mode with `filters={"appId": "..."}`.
11. Always include the currency basis for revenue content. If `list_currencies` returns one, use it as is; if several, have the user
    choose. If the result is empty, use `USD` as the default but state that it is a fallback.
12. `data_source` is not evidence of collection (some events are ingested even when it is empty). Use the `hive`/`custom`/
    `appsflyer` distinction only to judge who to ask for log improvements.
13. The recommendation catalog decides the scope of recommendations; the actual company metrics, events, and collection state decide
    the implementation approach and readiness. Do not delete a recommended content item because a log is missing — leave it under
    `not currently confirmed`.

## Result Format

First summarize each recommended dashboard's fit and the core rationale. Then provide the content mapping table.

| Content | Decision purpose | Metric or event | Mapping confidence | Properties strictly required to compute, break down, or filter this content | Metadata definition | Recent ingestion | Readiness | Next action |
|---|---|---|---|---|---|---|---|---|

Finally, organize everything into these three groups.

1. **Buildable now:** the rationale and the preview to confirm at the creation stage
2. **Possible with limits:** the missing optional properties and the feature limitations
3. **Not currently confirmed:** separated by reason across `EVENT_NOT_DEFINED`, `ATTRIBUTE_NOT_DEFINED`, `NO_RECENT_DATA`,
   `ATTRIBUTE_NO_DATA`, `FILTER_VALUE_UNVERIFIED`, `NO_DATA`, `DATA_CONTRACT_UNCONFIRMED`, and `QUERY_FAILED`

Do not expose the internal `company_cd`, `org_idx`, `workspace_idx`, or any idx values in the body. Present them separately only when
the user asks, for support or error reproduction.

These results are the final design review material. Even when there is an intent to create, do not switch to create-content in the
same response that presents the results. Build the follow-up context with `design_approval.approved=true` only after the user
explicitly approves the dashboard composition, the included and excluded items, the expected empty results, and the duplicate handling.
