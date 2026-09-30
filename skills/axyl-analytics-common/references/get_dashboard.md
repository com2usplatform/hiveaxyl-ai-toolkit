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

- **Do not judge duplication by the `content_idx` set of the member content.** Recreating the same composition
  copies the member content too, so a copy shares no idx at all with the original. Compare by `content_name`
  and the `metrics` sets.
- If the member-name set matches and `date_params` also matches, treat it as a copy: do not create it yet —
  present the existing URL and let the user choose reuse, create a copy, or skip (DUPLICATE_GATE).
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
