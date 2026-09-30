# get_content_template (Get Platform Content Template Detail)

Retrieves the saved configuration of one platform content template.

> **Prerequisite:** Follow [`../SKILL.md`](../SKILL.md). Take `template_idx` from
> `list_content_templates` or `get_dashboard_template`; do not guess it.

## When to Use

- After selecting a platform content template, to inspect the configuration needed by `preview_*` or `create_*`.
- When `get_dashboard_template.contents[]` has a valid `content_idx` but null name/type/chart metadata.
- To diagnose whether the target company has every metric, event, and dimension required by the template.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `company_cd` | Y | Company code confirmed by PROJECT_ID_GATE |
| `template_idx` | Y | Content template ID from a template list or dashboard-template member |
| `lang` | N | Translation language. Default: `ko` |
| `include_grid_config` | N | Include raw table display state. Default: `false` |

## Return Value

Returns `template_idx`, translated content name and description, `content_type`, `chart_type`, `mod_date`, and
company-resolved `params`. `params.unresolved_idx` lists references that have no target-company counterpart.

## Decision Rules

- Keep `include_grid_config=false` unless the raw table display state is required.
- For a dashboard member, this direct response is authoritative for its name, content type, chart type, and `params`.
  Null display metadata in the parent dashboard-template response does not invalidate this child reference.
- **The idx values in `params` are already resolved to the target company**, and each token's
  `text` / `name` / `measure_field` / `field` is updated to the company's name. Use them as given, and keep every
  other token field (such as `type`, `measure_formular`, `measure_group_format`, `measure_group_interval`) for the
  conversion in create-content's template_mapping.md. Just do not show raw token fields to the user.
- **Do not resolve names again.** Platform and company names can differ, so name matching either fails or
  silently picks a different metric or event.
- Entries with no counterpart in the company come back as `idx: null` with `unresolved: true`, and are collected
  in `params.unresolved_idx`.
- **Dimension names that carry no idx are validated, not swapped.** A funnel's `sections[].identifier` and a
  retention's `conditions[].base_dimension`/`retention_dimension` hold a name only. Platform and company
  dimension names are shared, so nothing is swapped — but the tool checks that
  the dimension actually exists on the resolved company event, and marks `{key}_unresolved: true` plus a
  `kind: "dimension_name"` entry in `params.unresolved_idx` when it does not (for example, a dimension that exists
  on the platform event but is not derived for the company). Never substitute a different dimension.
- **Filters are only resolved when `filter_type` is `index`, and only the dimension's idx is resolved — the filter values are
  left as the template wrote them**, so check them against this company's data before saving (template_mapping.md,
  "Dimension filters"). For `snapshot` and `segment` the `idx` is a
  snapshot or segment number, not a dimension, so it is left untouched — resolving it would blank out a working
  filter. Unknown filter types are left alone with a warning.
- **The template author's company and project are stripped from `params`** (`company_cd`, `companyCd`,
  `appid_group`, `game_name`, `project`). A stored template carries whoever created it — for example,
  `company_cd: <template_company_cd>` / `appid_group: "<template_appid_group>"` — and reusing those would build content against another
  company's project. Take the project from PROJECT_ID_GATE instead.
- If params parsing fails, leave the data contract unresolved instead of guessing.

## On Failure

- Missing template: return to `list_content_templates` or `get_dashboard_template` and select a valid ID.
- `unresolved_idx` present: do not substitute a similar item; exclude it with disclosure or prepare the missing schema.
  An unresolved **filter** dimension widens the population when excluded — say so and let the user choose.
- Authentication or API error: follow common authentication handling and report the server message.

## Recommended Chain

```text
PROJECT_ID_GATE → list_content_templates or get_dashboard_template
→ get_content_template → preview_* → DUPLICATE_GATE → WRITE_APPROVAL → create_*
```
