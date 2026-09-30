# create_metric (Register a Company Metric)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + **WRITE_APPROVAL** are required. Company permission is enough; Analytics administrator status is not required.
> `org_idx`/`workspace_idx` are **not** required — a metric belongs to the company, not to a workspace, so ORG_WORKSPACE_GATE does not apply.

## When to Use

Registering a metric is **never the first step**. Query in event mode with `preview_chart` first, and register only when one of these holds:

- The same aggregation will be reused across several charts or dashboards.
- A term needs **its own period** that differs from the chart period (stickiness = DAU / MAU, and the like) — this is only expressible inside a metric.
- The team wants the definition to appear in `list_metrics` so everyone builds charts from the same figure.

For a one-off number, stay in event mode. Do not register a metric just to answer a single question.

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

Each entry follows the **event mode** of `preview_chart` — `event_idx`, `event_name`, `dimension_idx`, `dimension_name`, `formular` are required, and per-term `filters`, calculated expressions (`operands`/`operators`), and two-stage rollup (`group_formular`/`group_format`/`group_interval`) all work the same way. Two differences:

- **Do not pass `currency` / `currency_dimension_name`.** A metric definition carries no currency; conversion is specified with `currency` on the chart that uses the metric. Passing it raises `ValidationError`.
- **Each term may carry `measure_date`** — its own aggregation period (see below).
- `alias` / `percent` / `decimal_point` belong to the tool arguments above, not to a measure entry.

Metric mode (`metric_idx`) is not supported inside a metric definition — express it with events.

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
- A metric is a company-wide asset, but the server checks only company permission (the same basis as `update_metric`).
  Do not require `check_analytics_admin`; because every project in the company sees the metric, state that scope when asking for approval.
- Check `list_metrics(company_cd)` for an equivalent metric first. The console stores any number of metrics with the same name, so an unchecked repeat of the request piles up duplicates.
- `group_formular` and `group_format` are specified together; `group_interval` only with `group_format="MINUTE"`.
- There is no delete tool. State that a registered metric has to be removed from the console, and keep test registrations out of production companies.

## On Failure

- `ValidationError`: the message names the offending key. The common causes are a missing required key, `currency` inside a metric definition, `measure_date` without a valid `date_params` shape, and an incomplete rollup key set.
- API error: the server response is included in the message. Check it and correct the parameters.

## Recommended Chain

```
(PROJECT_ID_GATE) → list_metrics (check for an equivalent metric)
→ list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart (validate the figures)
→ [WRITE_APPROVAL] → create_metric → preview_chart / create_chart (metric mode)
```
