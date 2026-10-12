# update_dashboard (Update Dashboard)

Updates a saved dashboard's name, description, member content, or global period and filters.
**This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL applies.

## When to Use

- To correct a dashboard name or description
- To add or remove content, or change the layout
- To attach a memo to a panel
- To set the dashboard's global period or filters

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx |
| `workspace_idx` | Y | Workspace the dashboard belongs to |
| `dashboard_idx` | Y | Dashboard idx to update (`list_contents` / `get_dashboard`) |
| `dashboard_name` | N | New name |
| `dashboard_desc` | N | New description |
| `contents` | N | New content list (in display order, one or more) |
| `date_params` | N | New global period |
| `adhoc_filters` | N | New global filters (applied to every member by dimension name; confirm every member's event has it). Passing `[]` removes them |

Each `contents` entry:

| Key | Required | Description |
|----|------|------|
| `content_idx` | Y (content panel) | Content idx in the same workspace |
| `content_type` | Y (content panel) | `chart`, `chart_rank`, `funnel`, `retention` |
| `chart_type` | N | Used only to decide the default size |
| `width` | N | Width on the 24-column grid. Defaults per type |
| `height` | N | Height. Defaults per type |
| `memo` | N | Panel memo. **Omit to keep the existing memo**, `""` to delete it |
| `row` | N | Row number from `get_dashboard`. A new row starts where the value changes |
| `panel_ref` | Y (text/image panel) | Panel number returned by `get_dashboard`. Such an entry has no `content_idx`/`content_type` |

**At least one** field to change is required.

## Built on a Full-Replace API

Reads the current dashboard, overwrites only what you pass, then sends the whole thing back.
Renaming does not require rebuilding the layout, and anything not passed — published state,
global settings, memos — is preserved.

## Passing contents Recalculates the Layout

To add or remove one content, check the current configuration with `get_dashboard` and pass the
**complete new list** in display order. **Carry over the `width`, `height`, and `row` that
`get_dashboard` returned to keep the existing layout.** Omit the sizes and each panel falls back to
its per-type default size, so sizes hand-tuned in the console revert. Omit `row` and entries fill one row until the
24 columns are used, so rows that were separate may merge.

## Text and Image Panels Are Not Deleted

This tool cannot create text or image panels or change their content, but rebuilding `contents` does not remove them either.

- To place a panel, put `{"panel_ref": n}` with the `panel_ref` from `get_dashboard` at that position (add `width`,
  `height`, and `row` to keep the original layout). The stored panel content is carried over as is.
- A panel not included in `contents` is **appended at the bottom with its original size and row grouping.**
- `panel_ref` numbers panels in display order (top to bottom, left to right). After moving panels, read the dashboard
  again with `get_dashboard` and use the new numbers before the next update.
- Delete a panel or change its content in the console.

Do not pass `contents` when you are only changing the name, description, or global settings.

## A Memo Belongs to a Panel

A memo is not a separate cell — it is a **field on a content cell**. So it disappears if it is
not carried over when `contents` is rebuilt. This tool **keeps the memo stored for that content
whenever an entry does not specify `memo`.** Pass `memo=""` to delete one.

## Global Period and Filters Apply to Every Panel

`date_params` and `adhoc_filters` are **dashboard-wide** and apply to every content inside it
(separate from each content's own period and filters).

For a fixed global period, write the dates as **date only, like `"2026-09-11"`** — unlike a
content's `date_params`, which uses `"2026-09-11 00:00:00"`. A time part is cut to the date.

## Return Value

`{"dashboard_idx", "dashboard_name", "changed", "console_url", "response"}`

- `changed`: names of the arguments actually changed in this call
- `console_url`: the updated dashboard screen. **Include it when reporting a write
  (POST_WRITE_LINK)**

## What This Tool Does Not Change

Published state (`published`) and folder placement are preserved but cannot be changed here.
Set them in the console.

## Decision Rules

- **Get user approval before calling (WRITE_APPROVAL).** When removing content, read back which
  ones are leaving, by name.
- **Removing content from a dashboard does not delete the content.** It stays in the workspace.
  Deletion is console-only.
- **Verify with `get_dashboard` after saving.** Do not judge from a success response alone.
- The only way back is to set the previous configuration again, so record the `get_dashboard`
  result before changing anything.

## On Failure

| Symptom | What to do |
|------|------|
| No field to change was passed | Ask the user which field to change |
| A content in `contents` belongs to another workspace | Only content in the same workspace can be attached |
| `content_type` does not match the stored type | Confirm the real type with `list_contents` / `get_content` |
| `width` greater than 24 | The grid is 24 columns |
| `panel_ref` out of range or used twice | Read the dashboard again with `get_dashboard` and check the panel numbers |
| Trying to add a new text or image panel | Not supported. Add it in the console |
| API error or session expiry | Do not retry automatically; check with `get_dashboard` whether it took effect |
| Dashboard created by someone else | Only a dashboard whose `get_dashboard` `permission` is `EDITOR` can be changed. Check it before saving any new content for the dashboard; otherwise ask the user whether to make a copy or request the change from the author |

## Recommended Chain

```text
get_dashboard (check configuration, layout, memos) → read back the changes → user approval
→ update_dashboard → verify with get_dashboard → report with console_url
```
