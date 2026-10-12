# create_metric (Register a Company Metric)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + **WRITE_APPROVAL** are required. Analytics administrator status is not required, but company permission and COMPANY MCP scope are.
> `org_idx`/`workspace_idx` are **not** required — a metric belongs to the company, not to a workspace, so ORG_WORKSPACE_GATE does not apply.

## When to Use

Unless the user explicitly asks to register a metric, registering is **never the first step**. Query in event mode with
`preview_chart` first, and register only when one of these holds:

- The same aggregation will be reused across several charts or dashboards.
- A term needs **its own period** that differs from the chart period (stickiness = DAU / MAU, and the like) — this is only expressible inside a metric.
- The team wants the definition to appear in `list_metrics` so everyone builds charts from the same figure.

For a one-off number, stay in event mode. Do not register a metric just to answer a single question.
When the user explicitly asks to register a metric, check `list_metrics` for an existing one first, then register it with
WRITE_APPROVAL. A request only to "show" a metric means a preview unless the user asks to save it.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `metric_name` | Y | Metric name. Appears as `metric_name` in `list_metrics` |
| `metric_category` | Y | Category. Call `list_metrics(company_cd)` first and reuse the value existing metrics use (a company may mix code values such as `"Sales"` with display values such as `"매출"` (Revenue)). Free text that the user fills in, so it is never used to decide whether a metric is revenue |
| `measures` | Y | Metrics to compute, usually one entry (see below) |
| `company_cd` | Y | Company code. `company_cd` from `list_projects` |
| `metric_description` | N | Description |
| `decimal_point` | N | Decimal places (default `null`) |
| `percent` | N | `"Y"` \| `"N"` (default `"N"`). Use `"Y"` for ratio metrics such as stickiness |
| `change_rate` | N | `"Y"` \| `"N"` (default `"N"`) |

Only event-based metrics are created (`create_type="EVENT"` is fixed). CSV-upload metrics are out of scope for this tool.

## measures Structure

Each `measures[]` entry has one of these two shapes.

- **Event measure:** `event_idx`, `event_name`, `dimension_idx`, `dimension_name`, and `formular` are required. Per-term
  `filters` and two-stage rollup (`group_formular`/`group_format`/`group_interval`) follow the event mode of
  `preview_chart`.
- **Calculated expression:** the outer entry contains `operands` and `operators`; it does not also need the five event
  keys above. Each operand is an event measure, a numeric constant, or a nested expression. At least one operand must
  ultimately be an event measure. Constants, nesting, operators, and division-by-zero rules follow `preview_chart`.

Metric-mode operands (`metric_idx`) are not supported anywhere inside a metric definition — expand them into event
measures. The remaining differences from chart measures are:

- **Do not pass `currency` / `currency_dimension_name`.** A metric definition carries no currency; conversion is specified with `currency` on the chart that uses the metric. Passing it raises `ValidationError`.
- **Each term may carry `measure_date`** — its own aggregation period (see below).
- `percent` / `decimal_point` belong to the tool arguments above, not to a measure entry. There is no `alias`;
  `metric_name` names the metric.

### measure_date (per-term period)

`measure_date` has the same shape as `date_params` in `preview_chart` (fixed `"F"` / relative `"V"`).

- When set, that term aggregates its **whole period into a single value**, and that value is spread as the **same constant across every date the chart selects** (for example, one MAU figure for 2026-08 shown identically on each September date).
- When omitted, that term follows the chart's own period (`date_params`) date by date.
- A metric definition is stored and reused, so prefer a **relative period (`"V"`)** — a fixed `"F"` window freezes the metric to those dates forever.

## Return Value

Returns `metric_idx`, `metric_name`, `metric_category`, `metric_config`, and `console_url`.

- Pass `metric_idx` and `metric_name` into the metric mode of `preview_chart` or
  `create_chart`.
- Reuse the returned `metric_config` when the chart needs the stored definition, especially for revenue handling.
- `console_url` links to the registered metric's detail screen. **Include it when reporting a write (POST_WRITE_LINK).**

## Decision Rules

- `event_idx` / `event_name` come from `list_events()`, and `dimension_idx` / `dimension_name` from `list_dimensions()`. Never invent them.
- Validate the figures with `preview_chart` in event mode **before** registering, then show the user the definition (event, dimension, aggregation, period, filters) and the name, and obtain WRITE_APPROVAL.
  A `measure_date` term cannot be previewed (`preview_chart` rejects it); check it as a separate chart over that period.
- A metric is a company-wide asset, so the server checks company permission and MCP access in that company (the same basis as `update_metric`).
  Do not require `check_analytics_admin`; because every project in the company sees the metric, state that scope when asking for approval.
- Check `list_metrics(company_cd)` for an equivalent metric first. The console stores any number of metrics with the same name, so an unchecked repeat of the request piles up duplicates.
- `group_formular` and `group_format` are specified together; `group_interval` only with `group_format="MINUTE"`.
- There is no delete tool. State that a registered metric has to be removed from the console, and keep test registrations out of production companies.

## On Failure

- `ValidationError`: the message names the offending key. The common causes are a missing required key, `currency` inside a metric definition, `measure_date` without a valid `date_params` shape, and an incomplete rollup key set.
- API error: the message carries only the HTTP status code. The first request may have succeeded, so check `list_metrics`
  for a metric with the same name. Count it as saved only when a metric that was not in the list before the save appeared
  with the approved definition; a same-name metric that existed before does not count. If one appeared, do not save again; otherwise retry only after fresh
  WRITE_APPROVAL (fix the parameters first if the error requires it).

## Recommended Chain

```
(PROJECT_ID_GATE) → list_metrics (check for an equivalent metric)
→ list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart (validate the figures)
→ [WRITE_APPROVAL] → create_metric → preview_chart / create_chart (metric mode)
```
