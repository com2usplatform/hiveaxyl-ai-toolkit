# Request Decomposition Patterns (natural language → content list)

Examples of decomposing a natural-language content or dashboard request into a list of `create_*` calls. **Confirm the actual metrics, events, and registered metrics through SCHEMA_FIRST** and do not guess them (NO_GUESSING). The metric names below are examples only.

Every dashboard example below is a request whose composition is already decided. A theme-only request such as
"make me a revenue dashboard" goes to axyl-design-dashboard first (SKILL.md Step 0-1b).

## Single content item (no dashboard)

```
"Save a revenue chart for the last 7 days"
→ [chart: Revenue (metric Sales, chart_type=line or table)]
→ return the content url from the create_chart result, with no dashboard assembly
```

## Ranking content

```
"Save a ranking of the top 10 products by revenue"
→ [chart_rank: revenue by product, dimensions=[productName], rank_limit=10, rank_order=desc]
```

## Revenue dashboard

```
"Make a revenue dashboard with total revenue, PU, the daily revenue trend, and revenue by country"
→ [
    chart·scorecard: Total revenue (KPI),
    chart·scorecard: PU,
    chart·line:      Daily revenue trend,
    chart·table:     Revenue breakdown by country (dimensions=[country])
  ]
```

## User / retention dashboard

```
"A dashboard with NU, the daily NU trend, and new-user retention"
→ [
    chart·scorecard: NU,
    chart·line:      Daily NU trend,
    retention:       NU retention (base_event=login+newUser=Y, retention_event=login, identifier=userId)
  ]
```

## Funnel dashboard

```
"A dashboard with an app launch → store entry → purchase funnel and the daily purchase conversion rate"
→ [
    funnel:     app launch → store entry → purchase,
    chart·line: Daily purchase conversion rate
  ]
```

## Decomposition Principles

- Always confirm metric names, events, registered metrics, and dimensions with `list_metrics`/`list_events`/`list_dimensions` before use.
- Verify each content item with its corresponding `preview_<type>` before saving, and obtain **WRITE_APPROVAL**.
- Content order = dashboard placement order. Placement sizes follow the dashboard layout policy (the 24-column grid).
- If the request is ambiguous (unclear metric, period, or project), confirm with the user rather than filling it in arbitrarily.
