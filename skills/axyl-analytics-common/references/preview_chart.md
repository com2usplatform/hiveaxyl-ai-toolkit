# preview_chart (Query Chart Data)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE are required.

## When to Use

- The **default entry point** for every metric query — DAU, revenue, event aggregations, and so on.
- Dimension breakdowns (by OS, by country, and so on) are also handled by this single tool through the `dimensions` parameter.
- **If the metric is registered in `list_metrics`, prefer metric mode.** (SCHEMA_FIRST)
  - Ordinary metric (DAU, and so on): `list_metrics(company_cd)` → `preview_chart`
  - Revenue metric (Sales, and so on): `list_metrics(company_cd)` + `list_currencies(company_cd)` → `preview_chart` (pass `metric_config` + `currency` together → `currency_options` is assembled automatically)
  - Unregistered metric: `list_events(company_cd)` → `list_dimensions(company_cd, event_name)` → `preview_chart`
- **Before calling, you must obtain `org_idx`/`workspace_idx` through ORG_WORKSPACE_GATE.** Passing an arbitrary value (for example, `0`) without obtaining them causes an authorization error.

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
| `dimensions` | N | Grouping basis. Each item **requires `idx`** (the `dimension_idx` from `list_dimensions`) plus `name`. For example, `[{"idx": <dimension_idx>, "name": "os", "name_alias": "OS"}]`. To group values into buckets, follow "Dimension buckets" below |
| `adhoc_filters` | N | List of query-wide filters (see below) |
| `content_name` | N | Content name (default `"preview"`) |
| `pivot_col_ids` | N | Names of dimensions to spread across columns in a table |
| `row_group_col_ids` | N | Names of columns to group rows by in a table |
| `aggregation` | N | Per-column aggregation settings for a table |
| `hidden_col_ids` | N | Names of columns to hide in a table |

- `pivot_col_ids`, `row_group_col_ids`, `aggregation`, and `hidden_col_ids` raise a `ValidationError` unless
  `chart_type="table"`. Column ids are display names: a measure's `alias` (otherwise its name), a dimension's `name_alias`
  (otherwise `name`), or `dateTime`.
- With pivot columns or row groups and no `aggregation`, every measure is summed. Do not sum unique-user counts or ratios
  across rows — pick `aggregation` per measure (for example, `{"Sales": "sum"}`).

### date_params structure

- `period`: `"D"` (day) | `"W"` (Monday–Sunday week) | `"M"` (calendar month, e.g. 2026-08) | `"H"` (hour) | `"MINUTE"` (minute — requires an added `minute_interval` field: 1, 2, 5, or 10)
- `start_date_type` / `end_date_type`: `"F"` (fixed date) | `"V"` (relative date, an offset from today)
- A fixed date (`"F"`) uses `start_date` / `end_date` in `YYYY-MM-DD HH:MM:SS` format, together with
  `"start_period": "D", "start_value": 0, "end_period": "D", "end_value": 0`. `end_date` is the last included day at
  `00:00:00` (last week = Monday `00:00:00` to Sunday `00:00:00`).
- A relative date (`"V"`) uses `start_value` / `end_value` (an integer offset in `start_period`/`end_period` units — `D` means
  days, for example `-7`) instead of `start_date` / `end_date`.
  Do not compute an absolute date and pass it in. Even if passed alongside, the MCP tool strips it.
- "Last week" means the last completed Monday–Sunday week; pass it as fixed dates (`F`). "The last 7 days" is a different
  range.
- For a distinct-count metric, `period` is also the counting window: query DAU with `"D"`. `"W"` returns weekly unique
  users, not DAU.

### event_measures structure

The two modes can be mixed. **Prefer metric mode** — pass any metric registered in `list_metrics` in metric mode.

#### Metric mode (when registered in `list_metrics` — preferred)

An ordinary metric uses `metric_idx` and `metric_name`. A revenue metric additionally passes the
confirmed `currency`.

- `metric_idx`: the `idx` from the `list_metrics()` result. Do not guess it.
- `metric_name`: the `metric_name` from the `list_metrics()` result (for display). Do not guess it.
- `metric_config`: optional. The `metric_config` string from the `list_metrics()` result; passing it saves a server lookup, and when omitted the server looks it up by `metric_idx`.
- `currency`: only for a revenue metric. For example, `"USD"` (confirm with `list_currencies`: one → use it; several → ask the user; empty → `"USD"`, and disclose the fallback)
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
- `formular`: `"COUNT_DISTINCT"` | `"COUNT"` | `"SUM"` | `"AVG"` | `"MIN"` | `"MAX"` (in a two-stage aggregation, this is the
  **first aggregation**)
  - `dimension_data_type` STRING → `COUNT` / `COUNT_DISTINCT`
  - `dimension_data_type` INT → `SUM` / `AVG` / `MIN` / `MAX` are also available
- `alias`: the metric name to display in the result
- `currency`: only for a revenue metric (`is_price=1`, and the event has an `is_currency=1` dimension). For example, `"USD"` (confirm with `list_currencies`: one → use it; several → ask the user; empty → `"USD"`, and disclose the fallback)
- `currency_dimension_name`: optional. The `dimension_name` of the dimension with `is_currency=1` in the `list_dimensions()` result; the server fills it when omitted

#### Measure options (both modes)

- `filters`: per-measure filters in the `[index]` adhoc filter format. They apply to that measure only, not to the whole
  query. NU is defined this way — AU with a `newUser=Y` filter; without the filter the measure equals AU, with no error.
- `percent`: `"Y"` | `"N"` (default `"N"`), whether to show the value as a percentage. `decimal_point`: number of decimal
  places (default `null`).
- Calculated measure: put the terms in `operands` (two or more) and the operators between them in `operators`
  (`"+"` | `"-"` | `"*"` | `"/"`, one fewer than `operands`). Each term is either a measure in metric or event mode (each
  with its own optional `filters`) or a numeric constant (for example, `100`, `0.6`) in any position (for example,
  `100 / AU`). At least one term must be a measure, and dividing by 0 is not allowed. Express parentheses by putting a
  sub-formula `{"operands": [...], "operators": [...]}` in a term's position (for example, `100 + AU + (PU * 0.6)` →
  `"operands": [100, AU, {"operands": [PU, 0.6], "operators": ["*"]}], "operators": ["+", "+"]`). A sub-formula holds
  only these two keys. Keep `alias`, `decimal_point`, and `percent` outside, at the measure level. Put `currency` on
  each revenue term inside `operands`, not on the outer measure. Only the first revenue term's conversion is applied, so
  do not combine revenue terms from different events in one formula — query them as separate measures. For a ratio already registered as a metric (ARPU, PU RATE, and so on), use that metric
  instead. A `measure_date` term cannot be used in a chart.

#### Two-stage aggregation (first aggregate by time unit → then fold again)

Use this for a metric such as peak concurrent users, which **first aggregates over a short time unit and then folds those
values into one**. Add the three keys below to an event-mode entry (they cannot be used in metric mode — express it through events).

| Key | Required | Description |
|----|------|------|
| `group_formular` | Y for two-stage | The second aggregation. `"MAX"` \| `"AVG"` \| `"LAST"` \| `"MIN"` |
| `group_format` | Y for two-stage | The bucket unit of the first aggregation. `"MINUTE"` \| `"H"` \| `"D"` \| `"M"` \| `"Y"` |
| `group_interval` | Y only when `group_format="MINUTE"` | Minute interval. `1` \| `2` \| `5` \| `10` |

- For example, peak concurrent users first counts distinct users over a short time unit, then folds it with a daily `MAX`.
- The first bucketing basis supports only `dateTime`, so do not specify it separately (the tool fills it in automatically).
- **The bucket the second aggregation folds over is decided by the chart axis (`date_params.period` / `dimensions`), not by the measure.**
  So `group_format` is meaningful only when it is **finer than** the chart's `period` — with a daily axis (`"D"`),
  a first bucket of `MINUTE`/`H` is right, whereas passing the same `"D"` as the axis makes the first and second buckets identical and the second aggregation meaningless.
- Specify `group_formular`/`group_format` **together**. Passing only one, or passing `group_interval` when the format is not
  `MINUTE`, raises a `ValidationError`.

### Dimension buckets

To view dimension values grouped under bucket labels, such as by payment amount range or by level range, add the keys
below to a `dimensions` entry. Use them in charts (`preview_chart`, `create_chart`, `update_chart`) and rankings
(`preview_chart_rank`, `create_chart_rank`, `update_chart_rank`). Buckets are set per query or chart; there is no saved
dimension-level bucket setting, so do not call `regist_event_dimension` to create them. Ask which query or chart to apply
them to.

| Key | Required | Description |
|----|------|------|
| `buckets` | Y when bucketing | List of buckets. Each bucket is either a value group `{"label", "values": [...]}` or a range `{"label", "min", "max"}` |
| `etc_label` | Y when bucketing | Label for values that fall into no bucket (including empty values) |
| `data_type` | N | The `dimension_data_type` from `list_dimensions`. When omitted, the tool looks it up by dimension idx. Used only for validation and not saved |

For example: `{"idx": <dimension_idx>, "name": "price", "data_type": "INT", "buckets": [{"label": "1~3", "min": 1,
"max": 3}, {"label": "4~5", "min": 4, "max": 5}], "etc_label": "Other"}`

- The available bucket kinds depend on the data type. `STRING` allows value groups only, `INT` allows both ranges and
  value groups, and `TIMESTAMP` allows no buckets.
- A range specifies both `min` and `max` and includes both ends (the bucket after `1~3` is `4~5`). Decimals are allowed.
- A value group's `values` are saved as strings (a number becomes `"7"`). Values for an `INT` dimension must be numbers (decimals allowed).
- Buckets are matched from the first one, so overlapping ranges, or the same value in more than one value group, raise a
  `ValidationError`.
- A monetary dimension is bucketed by the original amount, before currency conversion.
- Bucketing keeps the dimension's column name (`name_alias`), so do not change the table settings (`pivot_col_ids` and so on).
- A bucketed dimension read with `get_content` can be passed again as is (the tool fills in `data_type`).

### adhoc_filters structure

Use one of the three `filter_type` values.

#### [index] Direct event column filter (the most common)

- Use the `list_dimensions()` result for `idx`, `field`, and `data_type`.
- `adhoc_filters` applies to every measure by the dimension **name** (`field`), even when the measures come from
  different events. Take `idx`/`data_type` from any one measure's event (the console uses the first measure's event), and
  confirm with `list_dimensions` that every measure's event has a dimension with that name; if one does not, tell the user
  that measure may not be filtered and offer a per-measure filter instead.
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

- If a plain lookup gives no period, ask the user, or use the tool default (relative, `start_value=-8` to `end_value=-1`,
  from 8 days ago through yesterday) and say so.
- **Check first whether the metric is registered.** If the metric appears in the `list_metrics(company_cd)` result, use metric mode. Proceed in event mode only when it does not.
- **Judging whether it is a revenue metric:** only when the dimension that `metric_config` aggregates has `is_price=1` in `list_dimensions`
  and its event also has an `is_currency=1` dimension. Otherwise pass no `currency` and state that the amounts are not converted.
  A `measure_formular: "SUM"` token alone does not make it revenue — do not attach a currency to a non-monetary sum.
  - For a revenue metric, confirm the currency with `list_currencies(company_cd)` and pass `currency` as well.
    If there are several, ask the user; if the result is empty, use `"USD"` as the default and disclose that the fallback was applied.
  - Passing `metric_config` + `currency` together makes the server assemble `currency_options` automatically (including exchange-rate conversion).
  - Without a specified currency, a revenue metric is rejected with a validation error. Always state the currency.
- Take `event_idx` / `event_name` from the `list_events()` result and `dimension_idx` / `dimension_name` from the `list_dimensions()` result. Do not guess them.
- An event-mode revenue metric (an `is_price` dimension of an event that also has an `is_currency` dimension) must specify `currency`, taken from `list_currencies`. `currency_dimension_name` is optional.
- When you need a **first aggregation by time unit plus a second aggregation**, as with peak concurrent users, use the two-stage aggregation keys. Set
  `group_format` finer than the chart's `period` (with a daily axis, `MINUTE`/`H`).
- To register a two-stage aggregation as a metric, follow the cases in `create_metric`'s "When to Use" — including when the user
  explicitly asks to register it (a write — WRITE_APPROVAL).
- Handle dimension breakdowns with the `dimensions` parameter. No separate tool call is needed.
- Handle user filters with `adhoc_filters`.

## On Failure

- Empty result: check that `project` and the date range are correct.
- Organization or workspace authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- Other API error (parameter or validation): the error message includes the server response. Read it and fix the parameters.

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

`(ORG_WORKSPACE_GATE)` = `check_analytics_admin(company_cd)` → `list_organizations` → `list_projects(company_cd, org_idx)` →
`list_workspaces`; steps already done by PROJECT_ID_GATE are reused.
For the detailed steps, see `check_analytics_admin`, `list_organizations`, and `list_workspaces`.
