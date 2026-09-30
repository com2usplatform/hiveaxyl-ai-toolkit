# create_chart (Save Chart Content)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE + **WRITE_APPROVAL** are required.

## When to Use

- When the user wants to **save** a chart or create content for a dashboard.
- Before saving, always show the data with `preview_chart` and obtain **WRITE_APPROVAL** (explicit approval).

## Parameters

All query parameters follow `preview_chart`: `project`, `chart_type`, `date_params`,
`event_measures`, `company_cd`, `org_idx`, `workspace_idx`, `dimensions`, `adhoc_filters`, and the optional table
configuration fields. The create-only parameters are:

| Parameter | Required | Description |
|---|---|---|
| `content_name` | N | Saved content name. Default: `"chart"` |
| `content_description` | N | Saved content description. Default: empty string |

## create-Specific Details

- If `chart_type="table"`, the server automatically includes the default `grid_config` (no separate value is needed).
- `content_name`: Name of the content to save (default: `"chart"`). A meaningful name that reflects the user's intent is recommended.
- `content_description`: Optional.
- `org_idx` is accepted only for authorization and is not included in the saved body.

## Return Value

Returns the saved content ID, type, name, and Analytics console URL.

- `content_idx`: Pass it unchanged in `create_dashboard.contents`.
- `url`: Console link (POST_WRITE_LINK). Return it to the user.

## Decision Rules

- Run `preview_chart` with the same configuration before saving.
- Apply DUPLICATE_GATE and obtain WRITE_APPROVAL after presenting the preview and target workspace.
- A successful call creates a new asset; it does not update an existing content item.

## On Failure

- Parameter or schema error: correct the corresponding `preview_chart` configuration and preview again.
- Permission or workspace error: repeat ORG_WORKSPACE_GATE and do not retry with a guessed identifier.
- Save API error: report the server response and do not automatically retry, because the first request may have succeeded.

## Recommended Chain

```
(PROJECT_ID_GATE) → (SCHEMA_FIRST: list_metrics or list_events/list_dimensions)
→ (ORG_WORKSPACE_GATE) → preview_chart (validation) → [WRITE_APPROVAL] → create_chart
```
