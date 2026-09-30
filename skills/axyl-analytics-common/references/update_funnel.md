# update_funnel (Update Funnel)

Updates a saved funnel (`content_type='funnel'`). **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL applies.

## When to Use

- To add, remove, or reorder funnel steps
- To adjust the standard period (`standard_days`) or tracking period (`tracking_days`)
- To correct the name, description, period, or target project

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx |
| `workspace_idx` | Y | Workspace the content belongs to |
| `content_idx` | Y | Content idx to update |
| `content_name` | N | New name |
| `content_description` | N | New description |
| `project` | N | New target project list. **A funnel uses only the first entry** (single-project content) |
| `chart_type` | N | New chart type (`table`, `line`) |
| `date_params` | N | New period. Same format as `preview_funnel` |
| `sections` | N | New step list. Same format as `preview_funnel` |
| `compare_type` | N | Comparison basis |
| `standard_days` | N | Standard days |
| `tracking_days` | N | Tracking days |
| `convert_type` | N | Conversion display mode |
| `user_display_type` | N | User display mode |

**At least one** field to change is required.

## Built on a Full-Replace API

Reads the current content, overwrites only what you pass, then sends the whole thing back.
Passing `sections` **replaces the entire step list** — to add or remove one step, check the
current configuration with `get_content` and pass the complete new list in display order.

## Reordering Steps Rebuilds the Structure

**The first step and later steps are stored differently.** The first uses `identifier`; later
steps use `target_identifier`. If removing or reordering changes which step is first, this
structure is recalculated automatically, so the caller only needs to get the order right.

Each step also stores `event_name`. `table_description` is a human-readable note and defaults to
empty (the console usually leaves it blank too).

## The Target Project Is Stored in Two Places

A funnel keeps its project both in the content body and in `params.appid_group`. Passing
`project` **updates both**, so there is nothing to reconcile by hand.

## Return Value

Same shape as `update_chart`, with `content_type` of `"funnel"`.
**Include `console_url` when reporting a write (POST_WRITE_LINK)**.

## Decision Rules

- **Get user approval before calling (WRITE_APPROVAL).**
- **When changing settings, verify with `preview_funnel` first.** There is no undo tool.
- **Verify with `get_content` after saving.** Do not judge from a success response alone.
- **Look up each step's `event_idx` again with `list_events`.** Do not reuse an idx you
  remembered from an earlier lookup.
- Switching from a fixed period (`ep`, `F`) to a relative one (`V`) drops any previously stored
  absolute dates.

## On Failure

| Symptom | What to do |
|------|------|
| No field to change was passed | Ask the user which field to change |
| `sections` passed as an empty list | A funnel needs steps |
| Wrong content type | Use the tool for that type |
| Project outside the organization's scope | Check with `list_projects(company_cd, org_idx)` |
| Content created by someone else | A workspace member can only edit **content they created**. If `get_content.permission` is not `EDITOR` the save is rejected — ask the user whether to make a copy or request the change from the author |

## Recommended Chain

```text
list_events (confirm step event idx) → get_content (check current configuration)
→ preview_funnel (if settings change) → user approval
→ update_funnel → verify with get_content → report with console_url
```
