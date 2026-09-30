# preview_chart_rank (Query Ranked Content)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE +
> ORG_WORKSPACE_GATE + SCHEMA_FIRST are required.

## When to Use

- Use this to aggregate a metric by dimension value — user, product, country, and so on — and view the top or bottom ranks.
- `event_measures`, `date_params`, `adhoc_filters`, and the table settings follow the `preview_chart` contract exactly.
- Unlike an ordinary chart, this requires at least one `dimensions` entry as the ranking basis.

## Parameters

`project`, `date_params`, `event_measures`, `company_cd`, `org_idx`, `workspace_idx`, `adhoc_filters`,
`content_name`, and the table settings follow `preview_chart`. The arguments that ranking adds, or that carry
different constraints, are as follows.

| Parameter | Required | Description |
|---|---|---|
| `dimensions` | Y | List of dimensions to rank by. At least one |
| `rank_limit` | N | Number of ranks to display. 1 or more, default 10 |
| `rank_order` | N | `desc` (largest first, the default) or `asc` |
| `rank_tie_mode` | N | `sequence` / `rank` / `dense` |
| `rank_group_mode` | N | `combined` or `perDimension` |
| `chart_type` | N | Default `table` |

- `rank_tie_mode="sequence"`: assigns 1, 2, 3 in order even for ties.
- `rank_tie_mode="rank"`: ties share a rank and the next rank is skipped (1, 1, 3).
- `rank_tie_mode="dense"`: the rank after a tie continues without a gap (1, 1, 2).
- With a single dimension, use only `rank_group_mode="combined"`. With two or more, `perDimension` computes ranks
  separately for each dimension.

## Return Value

Returns the Analytics query API response object. `rank_limit` is a display setting that will be saved; it does not
itself limit the number of rows returned.

## Decision Rules

- `rank_limit` is a console display setting and does not limit the response rows themselves. For a high-cardinality dimension
  such as user ID, narrow the period and `adhoc_filters`.
- `dimensions` needs at least one entry, and must use values confirmed from `list_dimensions`.
- For a revenue ranking, confirm the currency per `list_currencies`.
- Do not save immediately when the query result is empty. Recheck the project, period, and configuration, and hand off to
  `create_chart_rank` only with the empty-content warning and WRITE_APPROVAL.

## On Failure

- Empty result: check the project, period, filters, and dimension cardinality.
- Ranking validation error: fix the combination of `rank_limit`, `rank_order`, `rank_tie_mode`, and `rank_group_mode`.
- Authorization error: perform ORG_WORKSPACE_GATE again.
- API error: fix the offending parameter named in the server message, then query again.

## Recommended Chain

```
(PROJECT_ID_GATE) → (SCHEMA_FIRST) → (ORG_WORKSPACE_GATE)
→ preview_chart_rank → (DUPLICATE_GATE) → [WRITE_APPROVAL] → create_chart_rank
```
