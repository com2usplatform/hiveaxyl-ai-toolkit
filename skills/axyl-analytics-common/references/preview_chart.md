# preview_chart (Query Chart Data)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE are required.

## When to Use

- The **default entry point** for every metric query — DAU, revenue, event aggregations, and so on.
- Dimension breakdowns (by OS, by country, and so on) are also handled by this single tool through the `dimensions` parameter.
- **If the metric is registered in `list_metrics`, prefer metric mode.** (SCHEMA_FIRST)
  - Ordinary metric (DAU, and so on): `list_metrics(company_cd)` → `preview_chart`
  - Revenue metric (Sales, and so on): `list_metrics(company_cd)` + `list_currencies(company_cd)` → `preview_chart` (pass `metric_config` + `currency` together → `currency_options` is assembled automatically)
  - Unregistered metric: `list_events(company_cd)` → `list_dimensions(company_cd, event_name)` → `preview_chart`
- **Before calling, you must obtain `org_idx`/`workspace_idx` through ORG_WORKSPACE_GATE, starting with `check_analytics_admin`.** Passing an arbitrary value (for example, `0`) without obtaining them causes an authorization error.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `project` | Y | List of project IDs. For example, `["com.example.game"]` |
| `chart_type` | Y | `"table"` \| `"scorecard"` \| `"line"` \| `"column"` \| `"bar"` \| `"pie"` |
| `date_params` | Y | Date range dict (see below) |
| `event_measures` | Y | List of metrics to query (see below) |
| `company_cd` | Y | Company code. The `company_cd` from `list_projects` |
| `org_idx` | Y | Organization idx. Obtained through ORG_WORKSPACE_GATE (the `idx` from `list_organizations`) |
| `workspace_idx` | Y | Workspace idx. Obtained through ORG_WORKSPACE_GATE (the `workspace_idx` from `list_workspaces`) |
| `dimensions` | N | Grouping basis. Each item **requires `idx`** (the `dimension_idx` from `list_dimensions`) plus `name`. For example, `[{"idx": <dimension_idx>, "name": "os", "name_alias": "OS"}]` |
| `adhoc_filters` | N | List of query-wide filters (see below) |
| `content_name` | N | Content name (default `"preview"`) |
| `pivot_col_ids` | N | Names of dimensions to spread across columns in a table |
| `row_group_col_ids` | N | Names of columns to group rows by in a table |
| `aggregation` | N | Per-column aggregation settings for a table |
| `hidden_col_ids` | N | Names of columns to hide in a table |

### date_params structure

- `period`: `"D"` (day) | `"W"` (Monday–Sunday week) | `"M"` (calendar month, e.g. 2026-08) | `"H"` (hour) | `"MINUTE"` (minute — requires an added `minute_interval` field: 1, 2, 5, or 10)
- `start_date_type` / `end_date_type`: `"F"` (fixed date) | `"V"` (relative date, an offset from today)
- A relative date (`"V"`) uses `start_value` / `end_value` (an integer offset, for example `-7`) instead of `start_date` / `end_date`.
  Do not compute an absolute date and pass it in. Even if passed alongside, the MCP tool strips it.

### event_measures structure

The two modes can be mixed. **Prefer metric mode** — pass any metric registered in `list_metrics` in metric mode.

#### Metric mode (when registered in `list_metrics` — preferred)

An ordinary metric uses `metric_idx` and `metric_name`. A revenue metric additionally passes the
confirmed `currency`.

- `metric_idx`: the `idx` from the `list_metrics()` result. Do not guess it.
- `metric_name`: the `metric_name` from the `list_metrics()` result (for display). Do not guess it.
- `metric_config`: optional. The `metric_config` string from the `list_metrics()` result; passing it saves a server lookup, and when omitted the server looks it up by `metric_idx`.
- `currency`: only for a revenue metric. For example, `"USD"` (confirm with `list_currencies`; if the result is empty, use `"USD"`)
- `alias`: the metric name to display in the result (if absent, `metric_name` is shown as is)

> **When the metric definition contains a per-term period or two-stage aggregation:** if an `expressions[]` entry in
> `metric_config` has `measure_date`, that entry **aggregates its whole period into a single value and enters every date
> the chart selected as the same constant** (the MAU term in stickiness). If it has `measure_group_field`/`measure_group_format`
> with a comma-joined `measure_formular` (`"COUNT_DISTINCT,MAX"`), it is a two-stage aggregation metric. Both are computed
> differently from the `date_params` the chart specifies, so if a number looks inconsistent with the period, check
> `metric_config` first and tell the user about that definition.

#### Event mode (for an unregistered metric or a custom aggregation)

The required keys are `event_idx`, `event_name`, `dimension_idx`, `dimension_name`, and `formular`. Do not copy the internal
tokens of a saved `metric_config` — build them from the `list_events` and `list_dimensions` results.

- `event_idx`, `event_name`: take them from the `list_events()` result. Do not guess.
- `dimension_idx`, `dimension_name`: take them from the `list_dimensions()` result. Do not guess.
- `formular`: `"COUNT_DISTINCT"` | `"COUNT"` | `"SUM"` | `"AVG"` (in a two-stage aggregation, this is the **first aggregation**)
  - `dimension_data_type` STRING → `COUNT` / `COUNT_DISTINCT`
  - `dimension_data_type` INT → `SUM` / `AVG` are also available
- `alias`: the metric name to display in the result
- `currency`: only for a revenue metric (`is_price=1`). For example, `"USD"` (confirm with `list_currencies`; if the result is empty, use `"USD"`)
- `currency_dimension_name`: optional. The `dimension_name` of the dimension with `is_currency=1` in the `list_dimensions()` result; the server fills it when omitted

#### Two-stage aggregation (first aggregate by time unit → then fold again)

Use this for a metric such as peak concurrent users, which **first aggregates over a short time unit and then folds those
values into one**. Add the three keys below to an event-mode entry (they cannot be used in metric mode — express it through events).

| Key | Required | Description |
|----|------|------|
| `group_formular` | Y for two-stage | The second aggregation. `"MAX"` \| `"AVG"` \| `"LAST"` |
| `group_format` | Y for two-stage | The bucket unit of the first aggregation. `"MINUTE"` \| `"H"` \| `"D"` \| `"M"` \| `"Y"` |
| `group_interval` | Y only when `group_format="MINUTE"` | Minute interval. `1` \| `2` \| `5` \| `10` |

- For example, peak concurrent users first counts distinct users over a short time unit, then folds it with a daily `MAX`.
- The first bucketing basis supports only `dateTime`, so do not specify it separately (the tool fills it in automatically).
- **The bucket the second aggregation folds over is decided by the chart axis (`date_params.period` / `dimensions`), not by the measure.**
  So `group_format` is meaningful only when it is **finer than** the chart's `period` — with a daily axis (`"D"`),
  a first bucket of `MINUTE`/`H` is right, whereas passing the same `"D"` as the axis makes the first and second buckets identical and the second aggregation meaningless.
- Specify `group_formular`/`group_format` **together**. Passing only one, or passing `group_interval` when the format is not
  `MINUTE`, raises a `ValidationError`.

### adhoc_filters structure

Use one of the three `filter_type` values.

#### [index] Direct event column filter (the most common)

- Use the `list_dimensions()` result for `idx`, `field`, and `data_type`.
- `value`: a list of values (for example, `["GO"]`). Omit it for a unary operator such as `not_null`.
- `value_expression`: `"select"` repeated once per value, joined with `", "` (for example, 1 value → `"select"`, 2 values → `"select, select"`)

#### [snapshot] Segment snapshot (a user set fixed at a point in time)

Use the snapshot and segment IDs confirmed from `list_segment_snapshots`. `operator` is `"eq"` (include) or
`"ne"` (exclude).

#### [segment] Real-time segment

Same as snapshot, but with `"filter_type": "segment"` and no `segment_idx` field.

## Return Value

Returns the Analytics query API response object. The time-series, dimension, and metric columns and the row structure vary with
the chosen `chart_type`, `event_measures`, and `dimensions`.

- Use the returned figures and the server-provided display names exactly as given.
- Empty data can still be a normal response, so do not read it as a successful save or as completed collection.

## Decision Rules

- **Check first whether the metric is registered.** If the metric appears in the `list_metrics(company_cd)` result, use metric mode. Proceed in event mode only when it does not.
- **Judging whether it is a revenue metric:** only when the dimension that `metric_config` aggregates has `is_price=1` in `list_dimensions`.
  A `measure_formular: "SUM"` token alone does not make it revenue — do not attach a currency to a non-monetary sum.
  - For a revenue metric, confirm the currency with `list_currencies(company_cd)` and pass `currency` as well.
    If the result is empty, use `"USD"` as the default and disclose that the fallback was applied.
  - Passing `metric_config` + `currency` together makes the server assemble `currency_options` automatically (including exchange-rate conversion).
  - Without a specified currency it is handled as a raw SUM (a mixed-currency total). Always state the currency.
- Take `event_idx` / `event_name` from the `list_events()` result and `dimension_idx` / `dimension_name` from the `list_dimensions()` result. Do not guess them.
- An event-mode revenue metric (an `is_price` dimension) must specify `currency`, taken from `list_currencies`. `currency_dimension_name` is optional.
- When you need a **first aggregation by time unit plus a second aggregation**, as with peak concurrent users, use the two-stage aggregation keys. Set
  `group_format` finer than the chart's `period` (with a daily axis, `MINUTE`/`H`).
- If the same two-stage aggregation will be reused across several charts, or a term needs its own period, register it as a metric with
  `create_metric` (a write — WRITE_APPROVAL). See `create_metric`.
- Handle dimension breakdowns with the `dimensions` parameter. No separate tool call is needed.
- Handle user filters with `adhoc_filters`.

## On Failure

- Empty result: check that `project` and the date range are correct.
- API error: the error message includes the server response. Read the message and fix the parameters.

## Recommended Chain

```
[Ordinary metric — DAU, PU, and so on]
list_projects → list_metrics → (ORG_WORKSPACE_GATE) → preview_chart (metric_idx + metric_name)

[Revenue metric — Sales, ARPU, and so on]
list_projects → list_metrics + list_currencies → (ORG_WORKSPACE_GATE) → preview_chart
  (metric_idx + metric_name + metric_config + currency)

[Event mode — when the metric is unregistered]
list_projects → list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart
list_events → list_dimensions → preview_chart (dimension breakdown via dimensions)
list_events → list_dimensions → preview_chart (user filter via adhoc_filters)
```

`(ORG_WORKSPACE_GATE)` = `check_analytics_admin(company_cd)` → `list_organizations` → `list_workspaces`.
For the detailed steps, see `check_analytics_admin`, `list_organizations`, and `list_workspaces`.
