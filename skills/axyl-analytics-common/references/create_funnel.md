# create_funnel (Save Funnel Content)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE + **WRITE_APPROVAL** are required.

## When to Use

- When the user wants to **save** a funnel or create funnel content for a dashboard.
- Before saving, always show the data with `preview_funnel` and obtain **WRITE_APPROVAL**.

## Parameters

All query parameters follow `preview_funnel`: `project`, `date_params`, `sections`,
`company_cd`, `org_idx`, `workspace_idx`, `chart_type`, `compare_type`, `standard_days`, `tracking_days`,
`convert_type`, and `user_display_type`. The create-only parameters are:

| Parameter | Required | Description |
|---|---|---|
| `content_name` | N | Saved content name. Default: `"funnel"` |
| `content_description` | N | Saved content description. Default: empty string |

## create-Specific Details

- If `chart_type="table"`, the server automatically includes the default `grid_config` (no separate value is needed).
- `content_name`: Name of the content to save (default: `"funnel"`). A meaningful name is recommended.
- `content_description`: Optional.
- `org_idx` is accepted only for authorization and is not included in the saved body.

## Return Value

Returns the saved content ID, type (`funnel`), name, and Analytics console URL.

- `content_idx`: Pass it unchanged in `create_dashboard.contents`.
- `url`: Console link (POST_WRITE_LINK).

## Decision Rules

- Run `preview_funnel` with the same steps and settings before saving.
- Apply DUPLICATE_GATE and obtain WRITE_APPROVAL after presenting the preview and target workspace.
- Keep the order and identifiers of all funnel sections unchanged between preview and save.

## On Failure

- Section or date validation error: correct the `preview_funnel` configuration and preview again.
- Permission error: repeat ORG_WORKSPACE_GATE.
- Save API error: do not automatically retry; use `list_contents` to check whether an asset was created.

## Recommended Chain

```
(PROJECT_ID_GATE) → (SCHEMA_FIRST: list_events/list_dimensions)
→ (ORG_WORKSPACE_GATE) → preview_funnel (validation) → [WRITE_APPROVAL] → create_funnel
```
