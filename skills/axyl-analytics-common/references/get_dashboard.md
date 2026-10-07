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

## Decision Rules

- The returned member list (`content_name`, `metrics`) and `date_params` are what a duplicate check compares; a
  recreated dashboard copies its members, so member `content_idx` values never match the original.
- If the composition only partially overlaps, offer to add the missing content to the existing dashboard, create a
  separate copy, or skip. To add or remove content, pass the full new list to `update_dashboard` after WRITE_APPROVAL,
  carrying over the `width`/`height`/`memo` this tool returned so the existing layout is kept.
- `create_dashboard` also accepts `width`/`height`/`memo` per item; pass these values to recreate the same layout.

## On Failure

- Missing candidate or wrong asset kind: return to `list_contents` and select a row with `kind="dashboard"`.
- Workspace mismatch or permission error: repeat ORG_WORKSPACE_GATE for the candidate's workspace.
- Empty or malformed detail: report that exact comparison is unavailable; do not declare a duplicate from the list row.

## Recommended Chain

```text
ORG_WORKSPACE_GATE → list_contents → get_dashboard(candidate dashboard_idx)
→ if needed get_content for member details → compare composition
```
