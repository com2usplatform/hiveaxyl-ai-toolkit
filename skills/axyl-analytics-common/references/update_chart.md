# update_chart (Update Chart)

Updates a saved chart (`content_type='chart'`). **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL applies.

## When to Use

- To correct a content name or description
- To change the period, measures, dimensions, or filters
- To change the chart type or adjust table display settings (pivot, row group, aggregation, hidden)

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx (`list_organizations.idx`) |
| `workspace_idx` | Y | Workspace the content belongs to |
| `content_idx` | Y | Content idx to update (`list_contents` / `get_content`) |
| `content_name` | N | New name |
| `content_description` | N | New description |
| `project` | N | New target project list (`appid_group`) |
| `chart_type` | N | New chart type (`table`, `line`, `pie`, `scorecard`, ...) |
| `date_params` | N | New period. Same format as `preview_chart` |
| `event_measures` | N | New measure list. Same format as `preview_chart` |
| `dimensions` | N | New dimension list |
| `adhoc_filters` | N | New filter list |
| `pivot_col_ids` | N | Table pivot columns. Only with `chart_type='table'` |
| `row_group_col_ids` | N | Table row group columns. Same restriction |
| `aggregation` | N | Table aggregation `{col_id: agg_func}`. Same restriction |
| `hidden_col_ids` | N | Table hidden columns. Same restriction |

**At least one** field to change is required.

## Built on a Full-Replace API

The server's update API takes the **entire** content. This tool **reads the current content
first, overwrites only what you pass, then sends the whole thing back.** Renaming does not
require reassembling measures and dimensions, and anything not passed is preserved — including
console display state such as column widths and sorting.

## A List You Pass Replaces That List Entirely

`event_measures`, `dimensions`, and `adhoc_filters` are **full replacements, not additions**.
To add one dimension, check the current list with `get_content` and pass the **complete new list**.

## Return Value

`{"content_idx", "content_type", "content_name", "changed", "console_url", "response"}`

- `changed`: names of the arguments actually changed in this call
- `console_url`: console screen for the updated content. **Include it when reporting a write
  (POST_WRITE_LINK)**

## Decision Rules

- **Get user approval before calling (WRITE_APPROVAL).** Read back what changes from what.
- **When changing settings, verify with `preview_chart` first.** There is no tool to undo a
  saved content. The only way back is to set the previous values again, so record them first.
- **Editing content attached to a dashboard also changes that dashboard.** State the blast
  radius up front.
- **Verify with `get_content` after saving.** Do not treat a success response as proof.
- **A dimension's `name_alias` is the console's dimension label.** Omit it and it is filled from
  `name`, which is usually what you want.

## Table col_id Values Are Display Names

The `col_id` values in `aggregation`, `pivot_col_ids`, `row_group_col_ids`, and `hidden_col_ids`
are all **display names** — `alias` for measures, `name_alias` (or `name` if omitted) for
dimensions, and `dateTime` for the date axis.

So **changing a measure's `alias` or a dimension breaks any table setting that referenced the old
name.** Pass the matching grid argument along with the change; if you do not, the call is
rejected before saving (the error lists what broke and which columns are available).

## On Failure

| Symptom | What to do |
|------|------|
| No field to change was passed | Ask the user which field to change |
| Wrong content type | Use `update_chart_rank`, `update_funnel`, or `update_retention` |
| Table setting points at a missing column | Read the column list in the error and pass the grid argument too |
| Project outside the organization's scope | Only projects the organization can access are allowed. Check with `list_projects(company_cd, org_idx)` |
| Grid argument passed for a non-table chart | Only available with `chart_type='table'` |
| Content created by someone else | A workspace member can only edit **content they created**. If `get_content.permission` is not `EDITOR` the save is rejected — ask the user whether to make a copy or request the change from the author |

## Recommended Chain

```text
get_content (check current settings) → state blast radius → preview_chart (if settings change)
→ user approval → update_chart → verify with get_content → report with console_url
```
