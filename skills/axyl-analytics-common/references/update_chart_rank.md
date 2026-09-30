# update_chart_rank (Update Ranking)

Updates a saved ranking (`content_type='chart_rank'`). **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL applies.

## When to Use

- To change the top N (`rank_limit`) or the sort direction
- To change the dimension the ranking is based on
- To correct the name, description, period, or measures

## Parameters

Takes the same parameters as `update_chart` (`company_cd`, `org_idx`, `workspace_idx`,
`content_idx`, `content_name`, `content_description`, `project`, `chart_type`, `date_params`,
`event_measures`, `adhoc_filters`, `pivot_col_ids`, `row_group_col_ids`, `aggregation`,
`hidden_col_ids`), plus ranking-specific fields.

| Parameter | Required | Description |
|---------|------|------|
| `dimensions` | N | New dimension list. **A ranking needs something to rank by, so it cannot be emptied** |
| `rank_limit` | N | New top N (1 or more) |
| `rank_order` | N | `desc` or `asc` |
| `rank_tie_mode` | N | Tie handling (`sequence`, `rank`, `dense`) |
| `rank_group_mode` | N | `combined` or `perDimension` |

**At least one** field to change is required.

## Built on a Full-Replace API

Same as `update_chart` — reads the current content, overwrites only what you pass, then sends
the whole thing back. `event_measures`, `dimensions`, and `adhoc_filters` replace that list
entirely when passed.

## Dimension Count and Group Mode Are Coupled

`rank_group_mode='perDimension'` requires **two or more dimensions**. Changing either one alone
can break the combination.

- Reducing to one dimension while leaving the mode → rejected before saving
- Pass `rank_group_mode='combined'` **together** with the change

The check runs against the **merged final state**, not just the arguments you passed, so a call
that only passes `dimensions` is still caught.

## Return Value

Same shape as `update_chart`, with `content_type` of `"chart_rank"`.
`console_url` points at the ranking detail screen (`/create/ranking?idx=`) — **include it when
reporting a write (POST_WRITE_LINK)**.

## Decision Rules

- **Get user approval before calling (WRITE_APPROVAL).**
- **When changing settings, verify with `preview_chart_rank` first.** There is no undo tool.
- **Verify with `get_content` after saving.**
- The `col_id` rules for table settings match `update_chart`, and a ranking table adds a
  **`순위` (rank) column**, so `순위` is also a valid `col_id`.

## On Failure

| Symptom | What to do |
|------|------|
| `perDimension` with only one dimension | Pass `rank_group_mode='combined'` as well |
| `dimensions` passed as an empty list | A ranking needs at least one dimension |
| `rank_limit` is 0 or less | Use an integer of 1 or more |
| Table setting points at a missing column | Read the column list in the error and pass the grid argument too |
| Content created by someone else | A workspace member can only edit **content they created**. If `get_content.permission` is not `EDITOR` the save is rejected — ask the user whether to make a copy or request the change from the author |

## Recommended Chain

```text
get_content (check current settings) → preview_chart_rank (if settings change) → user approval
→ update_chart_rank → verify with get_content → report with console_url
```
