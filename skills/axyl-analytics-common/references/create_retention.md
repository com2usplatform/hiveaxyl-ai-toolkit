# create_retention (Save Retention Content)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE + DUPLICATE_GATE + **WRITE_APPROVAL** are required.

## When to Use

- When the user wants to **save** retention content or create retention content for a dashboard.
- Before saving, always show the data with `preview_retention` and obtain **WRITE_APPROVAL**.

## Parameters

All query parameters follow `preview_retention`: `project`, `date_params`, `base_event`,
`retention_event`, `company_cd`, `org_idx`, `workspace_idx`, `identifier`, `chart_type`, `dimensions`,
`adhoc_filters`, and `display_format`. The create-only parameters are:

| Parameter | Required | Description |
|---|---|---|
| `content_name` | N | Saved content name. Default: `"retention"` |
| `content_description` | N | Saved content description. Default: empty string |

## create-Specific Details

- If `chart_type="table"`, the server automatically includes the default `grid_config` (no separate value is needed).
- `content_name`: Name of the content to save (default: `"retention"`). A meaningful name is recommended.
- `content_description`: Optional.
- `org_idx` is accepted only for authorization and is not included in the saved body.
- `dimensions` must come from `list_dimensions(company_cd, base_event.event_name)`. Only the save validates them — it
  rejects a dimension that is not on the base event, which `preview_retention` does not check.

## Return Value

Returns the saved content ID, type (`retention`), name, and Analytics console URL.

- `content_idx`: Pass it unchanged in `create_dashboard.contents`.
- `url`: Console link (POST_WRITE_LINK).

## Decision Rules

- Run `preview_retention` with the same cohort settings before saving.
- Apply DUPLICATE_GATE and obtain WRITE_APPROVAL after presenting the preview and target workspace.
- Keep the base event, retention event, identifier, dimensions, and filters unchanged between preview and save.

## On Failure

- Event, dimension, or date validation error: correct the preview configuration and preview again.
- Organization or workspace authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- Save API error, or the session expired during the call: do not automatically retry; use `list_contents` to check whether an asset was created before calling again. Use DUPLICATE_GATE's exact name/type recovery query (never `mine_only`; `limit=0` is allowed). An item that existed before the save does not count. Call again only after fresh WRITE_APPROVAL.

## Recommended Chain

```
(PROJECT_ID_GATE) → (SCHEMA_FIRST: list_events/list_dimensions)
→ (ORG_WORKSPACE_GATE) → preview_retention (validation) → (DUPLICATE_GATE) → [WRITE_APPROVAL] → create_retention
```
