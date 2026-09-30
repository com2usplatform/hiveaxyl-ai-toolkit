---
name: axyl-drill-down-metrics
metadata:
  version: "1.0.0"
description: |
  Breaks revenue and DAU down by dimension through preview_chart and ranks users through preview_chart_rank. "Segment breakdown"
  here means querying a metric split by dimension (OS, country, market) — not defining or saving a segment, which is
  axyl-create-segment.

  TRIGGER when:
  - The user asks for a revenue or DAU breakdown by OS, country, market, or product
  - The user asks for a segment analysis to find the cause of a revenue spike or drop
  - The user asks for a list of whale users or top-paying users

  DO NOT TRIGGER when:
  - The request is a simple DAU or revenue figure lookup → use preview_chart directly
  - The request investigates one specific user's activity, purchases, or logins → use axyl-inspect-user
  - The request is to create and save a segment or take a snapshot → axyl-create-segment
  - The request is development work unrelated to analytics
---

# axyl-drill-down-metrics

> **CRITICAL — Always review the common rules in [axyl-analytics-common](../axyl-analytics-common/SKILL.md) first.**
> **CRITICAL — Use only project_id and company_cd values confirmed through PROJECT_ID_GATE.**
> **CRITICAL — Use only org_idx and workspace_idx values confirmed through ORG_WORKSPACE_GATE (required for every preview_chart and preview_chart_rank call).**
> **CRITICAL — Always read the relevant `references/` document before calling each analysis pattern.**

---

## Analysis Patterns

### Segment breakdown
- [Dimension breakdown](references/dimension_breakdown.md) — use `preview_chart` with `dimensions` to break down by OS, country, market, and so on. Applies to any metric, not just DAU and revenue
- [User ranking](references/user_ranking.md) — use `preview_chart_rank` to aggregate and rank by userId. Ranking works with any metric, including payment amount and login count

---

## Workflow

### Prerequisite — Review the common rules

PROJECT_ID_GATE, ORG_WORKSPACE_GATE, SCHEMA_FIRST, and NO_GUESSING from axyl-analytics-common apply.
If project_id and company_cd have not been confirmed, perform PROJECT_ID_GATE first; if org_idx and workspace_idx have
not been confirmed, perform ORG_WORKSPACE_GATE first.

### Phase 1 — Verify the schema (SCHEMA_FIRST)

```
Step 1-0. Call list_metrics(company_cd)
  → if the metric to break down (DAU, revenue, ...) is registered, use metric mode in preview_chart
    so the numbers match the company's definition and the console; a revenue metric also needs currency
  → only when it is not registered, build the measure in event mode with Steps 1-1 and 1-2
  → either way, confirm the breakdown dimension with Step 1-2 (list_dimensions); for a registered metric, the event
    is the text of the {type:"event"} token in its metric_config (read it only — do not put tokens into event_measures)
  → user rankings (preview_chart_rank by userId) may use event mode directly

Step 1-1. Call list_events(company_cd)
  → confirm the event name and event_idx to use
  → can be skipped if the event name has already been confirmed

Step 1-2. Call list_dimensions(company_cd, event_name)
  → confirm the dimension name, dimension_idx, is_price, and is_currency to use
  → note the name and idx to use in dimensions or adhoc_filters
  → can be skipped if the dimension information has already been confirmed

Step 1-3. ORG_WORKSPACE_GATE (check_analytics_admin → list_organizations → list_workspaces)
  → obtain the org_idx/workspace_idx that preview_chart and preview_chart_rank require
  → can be skipped if the values have already been confirmed
```

### Phase 2 — Segment breakdown

```
Step 2-1. DAU breakdown     → preview_chart (dimensions=[{idx: <dimension_idx>, name: "os"|"country"|...}])
Step 2-2. Revenue breakdown → preview_chart (dimensions=[{idx: <dimension_idx>, name: "country"|"productName"|...}], with currency specified)
Step 2-3. User ranking      → preview_chart_rank
  (dimensions=[{idx: <dimension_idx>, name: "userId"}], set rank_limit/rank_order/rank_tie_mode/rank_group_mode)
```

> **Principle for presenting results:** Do not declare a cause from a single dimension breakdown.
> Express it as "the segment with the largest impact + the hypothesis to check."

### Phase 3 — Decide whether to hand off an individual-user investigation

```
Step 3. If the ranking result requires investigating one user's activity, purchases, or logins
  └─ pass the selected user_id and confirmed project scope to axyl-inspect-user.
  └─ Do not query individual-user history in this skill.
```

The full drill-down chain:
```
list_events → list_dimensions (verify the schema) → (ORG_WORKSPACE_GATE)
  └─ preview_chart (dimension breakdown)        ← Phase 2
       └─ preview_chart_rank (user ranking)     ← Phase 2
            └─ decide whether to hand off to axyl-inspect-user ← Phase 3
```

---

## Prohibited Behavior ❌

| Situation | Prohibited behavior | Correct behavior |
|------|----------|-----------|
| project_id unconfirmed | Running the drill-down right away | Perform PROJECT_ID_GATE, then retry |
| org_idx/workspace_idx unconfirmed | Calling preview_chart or preview_chart_rank with an arbitrary value (for example, 0) | Perform ORG_WORKSPACE_GATE, then retry |
| Specific-user investigation needed | Querying individual history in this skill | Pass the selected user_id and project scope to axyl-inspect-user |
| Dimension unclear | Guessing and passing it | Confirm with `list_dimensions`, then pass it |
| Displaying revenue | Showing only the number | Always display the currency basis alongside |
| Single dimension breakdown result | Declaring "the cause is X" | Express it as "the segment with the largest impact is X, and the hypothesis to check is Y" |

---

## Exception Handling

| Situation | Response |
|------|------|
| Dimension name error | Select the correct dimension_name from the list_dimensions result, then retry |
| Empty user ranking result | Explain that no user generated that metric in that period. Suggest widening the date range |
| Organization or workspace authorization error | Perform ORG_WORKSPACE_GATE again. Recheck accessible values with `list_organizations`/`list_workspaces` |
