# create_dashboard (Create Dashboard)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). ORG_WORKSPACE_GATE + **WRITE_APPROVAL** are required.

## When to Use

- When assembling content (`content_idx`) saved with `create_chart`/`create_chart_rank`/`create_funnel`/`create_retention` into one dashboard.
- If there is only one content item, you may return only the content URL without a dashboard — use a dashboard **to group multiple content items**.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `dashboard_name` | Y | Dashboard name |
| `contents` | Y | List of content to place, in display order. See below |
| `company_cd` | Y | Company code |
| `org_idx` | Y | Organization idx (used for authorization; not included in the dashboard body) |
| `workspace_idx` | Y | Workspace idx (the location where the dashboard will be created) |
| `dashboard_desc` | N | Description |

### contents Structure

```json
[
  {"content_idx": <content_idx>, "content_type": "chart", "chart_type": "table"},
  {"content_idx": <content_idx>, "content_type": "chart_rank", "chart_type": "table"},
  {"content_idx": <content_idx>, "content_type": "funnel"},
  {"content_idx": <content_idx>, "content_type": "retention"}
]
```

- `content_idx`: Value returned by `create_*`, or an existing content idx verified by `get_content` in the same
  organization and workspace. Do not guess (NO_GUESSING).
- `content_type`: `"chart"` | `"chart_rank"` | `"funnel"` | `"retention"`.
- `chart_type`: Used to determine placement size **only for charts** (`scorecard`/`table`/other). May be omitted.
- `width` / `height` / `memo`: optional. Width on the 24-column grid, height, and a cell memo. Omit them for the type's default
  size; pass the values from `get_dashboard` or `get_dashboard_template` to keep an existing layout.

## Layout

- Placement is **calculated automatically in `contents` order** (24-column grid). Size and
  placement rules by content type follow the dashboard layout policy (24-column grid) owned by
  the `axyl-create-content` skill.
- If the user wants a specific order (for example, KPIs at the top), reflect it in the `contents` order.

## Return Value

Returns the saved dashboard ID and the Analytics console URL.

- `url`: Console link (POST_WRITE_LINK). Return it to the user.

## Decision Rules

- Run DUPLICATE_GATE before creation and obtain WRITE_APPROVAL for the final content order and target workspace.
- Every `content_idx` must identify a saved content item in the same workspace, with the matching `content_type`.
- Preserve the requested display priority through `contents` order; placement coordinates are calculated by the server.
- This tool creates a new dashboard and cannot modify an existing one — use `update_dashboard` to change an existing dashboard.

## On Failure

- Empty or malformed `contents`: provide at least one valid content object and correct its type.
- Missing or mismatched content: verify it with `get_content` in the target workspace.
- Permission error: repeat ORG_WORKSPACE_GATE.
- Save API error: do not automatically retry; use `list_contents` to check whether the dashboard was created.

## Recommended Chain

```
create_chart / create_chart_rank / create_funnel / create_retention (× N, collect content_idx values)
→ [WRITE_APPROVAL] → create_dashboard(contents=[collected content_idx values in order])
```

The server rejects an empty `contents` list, unknown/mismatched content types, and content that does not belong
to the requested workspace.
