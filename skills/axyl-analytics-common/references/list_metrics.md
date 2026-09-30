# list_metrics (List Registered Metrics)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the first step of SCHEMA_FIRST.

## When to Use

- Before calling `preview_chart`, to check **first of all** whether the metric you want is already registered.
- If it is registered, prefer metric mode (`metric_idx`); move on to `list_events`/`list_dimensions` only when it is not.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |

## Return Value

For each metric, returns the `idx`, the category, the name and description, and the reusable definition (`metric_config`).

- `idx`: use as `preview_chart`'s `event_measures[].metric_idx`.
- `metric_category`: for example `"이용자"` (Users) | `"매출"` (Revenue) | `"컨텐츠"` (Content). Because the user fills this in by hand, do not judge the metric's kind from this value alone — use it together with `metric_config`.
- Determine whether it is a revenue metric **only** from `is_price=1` on the dimension that `metric_config` aggregates (see `list_dimensions`). The server applies the same standard when checking whether `currency` is required.
- `metric_name`: use as `preview_chart`'s `event_measures[].metric_name` (for display).
- `metric_config`: a JSON string. Pass it through to `preview_chart` only for a revenue metric (judged by `is_price=1` as above, not by a `SUM` token).
- A `measure[].expressions[]` entry in `metric_config` can contain either of the following. Both are computed differently from the period and aggregation the chart specifies, so if a number looks inconsistent with the period, check here first.
  - `measure_date`: the aggregation period for that entry alone. It aggregates that whole period into a single value, which enters **every date the chart selected as the same constant** (the MAU term in stickiness).
  - `measure_group_field`/`measure_group_format`/`measure_group_interval` plus a comma-joined `measure_formular` (`"COUNT_DISTINCT,MAX"`): two-stage aggregation (a first aggregation by time unit, then a second aggregation). Peak concurrent users takes this form.

- The common-metric link information is an internal value used for template substitution. `get_content_template` handles it, so the skill
  does not match it itself.

## Decision Rules

- If the metric name you want appears in `metric_name`, use metric mode (do not expand it by hand into event mode).
- Do not parse `metric_config` and put its internal tokens (`type`/`idx`/`text`, and so on) directly into `event_measures` — pass only `metric_idx`/`metric_name` (plus `metric_config` + `currency` for a revenue metric) and the server handles the rest internally.
- For a revenue metric, confirm the currency with `list_currencies(company_cd)` and pass `currency` as well.
- If the metric you want does not exist, query first with `preview_chart` in event mode. Register it with `create_metric` only when it will be reused across several charts or when a term needs its own period (stickiness and the like) (a write — WRITE_APPROVAL).

## On Failure

- Empty result: no metrics are registered. Proceed in event mode, in the order `list_events` → `list_dimensions`.

## Recommended Chain

```
[Ordinary metric] list_metrics → (ORG_WORKSPACE_GATE) → preview_chart (metric_idx + metric_name)
[Revenue metric]  list_metrics + list_currencies → (ORG_WORKSPACE_GATE) → preview_chart (metric_idx + metric_name + metric_config + currency)
[Unregistered]    list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart (event mode)
[Registering]     list_events → list_dimensions → preview_chart (verify) → [WRITE_APPROVAL] → create_metric
```
