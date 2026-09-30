# Dimension Breakdown (preview_chart + dimensions, general-purpose)

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md).

## When to Use

- To break **any metric** into segments — by OS, country, market, language, product, and so on. It is not limited to DAU and revenue; whatever metric you put in `event_measures`, the same mechanism (the `dimensions` parameter) applies.
- When you want to locate the cause of a sudden metric change in a particular dimension.

The pattern itself is the same regardless of the metric — just change `event_measures` to match the target metric. Below are two commonly used variants (DAU and revenue) as examples.

## Call Order

```
0. list_metrics(company_cd)                      → if the metric is registered, use metric mode; still run steps 1-2
                                                    for the metric's event to confirm the breakdown dimension
1. list_events(company_cd)                       → confirm the event_idx of the metric to break down
2. list_dimensions(company_cd, event_name)       → confirm the dimension to break down by (dimension_name, dimension_idx)
3. list_currencies(company_cd)                   → only for a revenue metric, confirm the currency code
4. (ORG_WORKSPACE_GATE)                          → obtain org_idx/workspace_idx
5. preview_chart(...)                            → break down by dimension via the dimensions parameter
```

> **Required keys:** `event_measures` needs all of `event_idx`/`event_name`/`dimension_idx`/`dimension_name`/`formular`.
> `preview_chart` also requires `company_cd`/`org_idx`/`workspace_idx`. For details, see
> `preview_chart`.

## preview_chart call example — DAU by OS

```json
{
  "project": ["com.example.game"],
  "chart_type": "bar",
  "date_params": {
    "period": "D",
    "start_date": "2026-06-01 00:00:00",
    "end_date": "2026-06-25 00:00:00",
    "start_date_type": "F",
    "end_date_type": "F",
    "start_period": "D", "start_value": 0,
    "end_period": "D",   "end_value": 0
  },
  "event_measures": [
    {
      "event_idx": <event_idx>,
      "event_name": "app_login",
      "dimension_idx": <dimension_idx>,
      "dimension_name": "userId",
      "formular": "COUNT_DISTINCT",
      "alias": "DAU"
    }
  ],
  "company_cd": <company_cd>,
  "org_idx": <org_idx>,
  "workspace_idx": <workspace_idx>,
  "dimensions": [
    {"idx": <dimension_idx>, "name": "os", "name_alias": "OS"}
  ]
}
```

## preview_chart call example — Revenue by country

```json
{
  "project": ["com.example.game"],
  "chart_type": "bar",
  "date_params": {
    "period": "D",
    "start_date": "2026-06-01 00:00:00",
    "end_date": "2026-06-25 00:00:00",
    "start_date_type": "F",
    "end_date_type": "F",
    "start_period": "D", "start_value": 0,
    "end_period": "D",   "end_value": 0
  },
  "event_measures": [
    {
      "event_idx": <event_idx>,
      "event_name": "product_purchase",
      "dimension_idx": <dimension_idx>,
      "dimension_name": "totalPrice",
      "formular": "SUM",
      "alias": "Revenue",
      "currency": "<list_currencies result>"
    }
  ],
  "company_cd": <company_cd>,
  "org_idx": <org_idx>,
  "workspace_idx": <workspace_idx>,
  "dimensions": [
    {"idx": <dimension_idx>, "name": "country", "name_alias": "Country"}
  ]
}
```

> Confirm `event_idx`/`dimension_idx` by calling `list_events`/`list_dimensions` for the target metric.
> To break down a different metric (a retention-related event, a specific action, and so on), just change
> `event_measures` to match that metric. For `org_idx`/`workspace_idx`, use the values obtained through
> ORG_WORKSPACE_GATE (`check_analytics_admin` → `list_organizations` → `list_workspaces`). The values above are
> examples only — do not use them as is.

A **two-stage aggregation** metric such as peak concurrent users breaks down the same way — just add
`group_formular`/`group_format`/`group_interval` to the `event_measures` entry (for example, the daily maximum of
2-minute concurrency by OS). The second aggregation applies per combination of the chart axis and `dimensions`, so
adding a breakdown dimension yields the maximum per that dimension.
The key formats and constraints follow the "Two-stage aggregation" section of `preview_chart`.

## Commonly Used Breakdown Dimensions

| Breakdown basis | `dimensions[].name` example |
|----------|--------------------------|
| OS | `"os"` |
| Country | `"country"` |
| Market | `"market"` |
| Language | `"language"` |
| Product name | `"productName"` |

> **Always confirm the actual dimension_name from the `list_dimensions` result. The examples above are for reference.**

## Principles for Interpreting Results

- **For revenue and other monetary metrics**, always display the currency basis alongside. (For example, 12,345 USD)
- Do not declare a cause from a single dimension breakdown.
- Express it as "the segment with the largest impact + the hypothesis to check."
- Example: "Android DAU fell the most, -15% week over week. Check whether there was an Android update or a store policy change."
- Example: "US revenue rose the most, +32% week over week. Check the marketing activity for that period."

## Recommended Chain

```
list_currencies (for a revenue metric) → list_events → list_dimensions → (ORG_WORKSPACE_GATE)
  → preview_chart (dimension breakdown) → preview_chart_rank (user ranking)
  → if a specific user needs investigation, hand off to axyl-inspect-user
```
