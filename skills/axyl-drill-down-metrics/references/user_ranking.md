# User Ranking Query (preview_chart_rank + userId dimensions, general-purpose)

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md).
> For detailed arguments and constraints, see the [preview_chart_rank tool contract](../../axyl-analytics-common/references/preview_chart_rank.md).

## When to Use

- To rank users by **any metric** and query the top or bottom N. It is not limited to payment amount; it works the same way for login count, occurrences of a specific event, item usage, and so on.
- Useful for identifying "whale users" (top spenders), the most frequent players, the most active users, users with anomalous behavior, VIP management, and so on.
- When one user needs further investigation, pass the selected `userId` to `axyl-inspect-user`.

The pattern itself is the same regardless of the metric — just change `event_measures`, set the per-user ranking basis
with `dimensions=[{idx: <dimension_idx>, name: "userId"}]`, and choose the ranking direction with `rank_order`.

## Call Order

```
1. list_events(company_cd)                   → confirm the event_idx of the ranking basis event
2. list_dimensions(company_cd, event_name)   → confirm the dimension to aggregate (dimension_idx)
3. list_currencies(company_cd)               → only for a revenue metric, confirm the currency code to use
4. (ORG_WORKSPACE_GATE)                      → obtain org_idx/workspace_idx
5. preview_chart_rank(...)                   → rank users with dimensions=[{idx: <dimension_idx>, name: "userId"}]
```

## preview_chart_rank call example — Top-paying users by revenue

```json
{
  "project": ["com.example.game"],
  "chart_type": "table",
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
      "alias": "Total Payment Amount",
      "currency": "<list_currencies result>"
    }
  ],
  "company_cd": <company_cd>,
  "org_idx": <org_idx>,
  "workspace_idx": <workspace_idx>,
  "dimensions": [
    {"idx": <dimension_idx>, "name": "userId", "name_alias": "User ID"}
  ],
  "rank_limit": 10,
  "rank_order": "desc",
  "rank_tie_mode": "rank",
  "rank_group_mode": "combined"
}
```

## preview_chart_rank call example — Most frequent players by login count (not revenue)

```json
{
  "project": ["com.example.game"],
  "chart_type": "table",
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
      "formular": "COUNT",
      "alias": "Login Count"
    }
  ],
  "company_cd": <company_cd>,
  "org_idx": <org_idx>,
  "workspace_idx": <workspace_idx>,
  "dimensions": [
    {"idx": <dimension_idx>, "name": "userId", "name_alias": "User ID"}
  ],
  "rank_limit": 10,
  "rank_order": "desc",
  "rank_tie_mode": "rank",
  "rank_group_mode": "combined"
}
```

> Confirm `event_idx`/`dimension_idx` by calling `list_events`/`list_dimensions` for the event you want to rank by.
> To rank by a different basis (item use count, occurrences of a specific action, and so on), just change
> `event_measures` to match that metric. For `org_idx`/`workspace_idx`, use the values obtained through
> ORG_WORKSPACE_GATE. The values above are examples only — do not use them as is.

> When `userId` is the only ranking dimension, use `rank_group_mode="combined"`.
> Use `rank_order="desc"` for the top N and `rank_order="asc"` for the bottom N.
> `rank_limit` is a console display setting and does not limit the number of rows returned. For a high-cardinality
> dimension such as userId, narrow the date range and `adhoc_filters`.

## Handling the Result

- Present the result as top (`desc`) or bottom (`asc`) ranks according to `rank_order`.
- **For revenue and other monetary metrics**, always display the currency basis alongside. (For example, 12,345 USD)
- To investigate one selected user's activity, purchases, or logins, hand off to `axyl-inspect-user`.
- This skill stops at ranking and does not query an individual user's activity history.

## Recommended Chain

```
list_currencies (for a revenue metric) → list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart_rank (user ranking)
                                                         └─ if needed, hand off to axyl-inspect-user
```
