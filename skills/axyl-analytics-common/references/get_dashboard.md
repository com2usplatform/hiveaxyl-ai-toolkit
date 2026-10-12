# get_dashboard (Get Saved Dashboard Detail)

Retrieve one saved dashboard's composition — which content items are placed, in what order and size.

> **Prerequisite:** Take `dashboard_idx` from a `list_contents` row with `kind="dashboard"` (NO_GUESSING).

## When to Use

- In DUPLICATE_GATE, to compare a dashboard candidate's composition.
- When adding content to an existing dashboard instead of creating a new one (read it first, then `update_dashboard`).
- When building a similar dashboard based on an existing one.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed with `list_projects` |
| `org_idx` | Y | Organization idx confirmed through the organization gate |
| `workspace_idx` | Y | Workspace idx from the candidate row; the server verifies membership and ownership |
| `dashboard_idx` | Y | Dashboard idx |

## Return Value

Returns dashboard identity and description, workspace and permission, global settings, ordered content cells with
layout hints, and the Analytics console URL.

- `chart_type` is always `null` (the list API does not provide it). Use `get_content` when you need it.
- `width` is on the 24-column grid — 12 is half a row, 24 is a full row.
- `permission`: only a dashboard with `EDITOR` can be changed with `update_dashboard`.
- `height` is the height of the row the cell belongs to. Cells with the same `row` sit side by side in one row.
- `cell_type` is `"content"`, `"text"`, or `"image"`. Text and image panels have `content_idx`/`content_type` of `null`,
  the body (text) or URL (image) in `content`, and in `panel_ref` the panel number to use with `update_dashboard`.

## Decision Rules

- In DUPLICATE_GATE, use the returned member list (`content_name`, `metrics`) only to narrow and pair candidates. Apply the
  **dashboard copy criteria defined in the common DUPLICATE_GATE**; do not redefine them here. This requires calling
  `get_content` for every content member (`cell_type="content"`) of each candidate dashboard being compared; text and image panels have no `content_idx`. Member `content_idx` values are not comparison evidence because a
  recreated dashboard copies its members.
- If the composition only partially overlaps, offer to add the missing content to the existing dashboard (only when
  `permission` is `EDITOR`), create a separate copy, or skip. To add or remove content, pass the full new list to `update_dashboard` after WRITE_APPROVAL,
  carrying over the `width`/`height`/`memo`/`row` this tool returned so the existing layout is kept. Pass text and image
  panels as `{"panel_ref": n}` (one left out is not deleted; it moves to the bottom).
- `create_dashboard` also accepts `width`/`height`/`memo`/`row` per item; pass these values to recreate the same layout. It cannot
  recreate text or image panels; tell the user to add them in the console.

## On Failure

- Missing candidate or wrong asset kind: return to `list_contents` and select a row with `kind="dashboard"`.
- Pass the workspace from the candidate's `list_contents` row. If you passed a different one, run ORG_WORKSPACE_GATE for
  the row's workspace and call again.
- Organization or workspace authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- Empty or malformed detail: report that exact comparison is unavailable; do not declare a duplicate from the list row.

## Recommended Chain

```text
ORG_WORKSPACE_GATE → list_contents → get_dashboard(candidate dashboard_idx)
→ get_content for every content member → apply the common DUPLICATE_GATE dashboard copy criteria
```
