# get_dashboard_template (Get Platform Dashboard Template Detail)

Retrieves one platform dashboard template selected from `list_dashboard_templates`.

> **Prerequisite:** Follow [`../SKILL.md`](../SKILL.md). Take `template_idx` from
> `list_dashboard_templates`; do not guess it.

## When to Use

- After narrowing dashboard templates, to inspect ordered member content and layout hints.
- Before requesting each member's data contract with `get_content_template`.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `company_cd` | Y | Company code confirmed by PROJECT_ID_GATE |
| `template_idx` | Y | Dashboard template ID from `list_dashboard_templates` |
| `lang` | N | Translation language. Default: `ko` |

## Return Value

Returns dashboard name, description, global date/filter settings, and ordered `contents`. Each content cell includes
its template ID, type, chart type, row/order, size, and optional memo. After joining the list metadata, if any child
metadata field is null and `content_idx` exists, the server directly looks up that child template and fills the null fields.

## Decision Rules

- `contents[]` is ordered and includes template content IDs and layout sizes.
- A memo cell can have `content_idx=null`; do not interpret it as content.
- `contents[].content_idx` is a content **template** ID. Use it only with `get_content_template`.
- For every `cell_type=content` cell with a non-null `content_idx`, call `get_content_template` before designing or
  judging feasibility. The child detail contains the actual content type, chart type, and `params` contract.
- If `content_name`, `content_type`, or `chart_type` is null while `content_idx` exists, look up that child directly
  and fill the null field. A field that remains null is **not by itself** evidence that the child was deleted, has no
  data, or cannot be created.
- `width`/`height` can be passed to `create_dashboard` per item to keep the template's layout; omit them for default sizes.

## On Failure

- Missing template: return to `list_dashboard_templates` and select a valid ID.
- Member name/type/chart type is null: call `get_content_template` with that member's `content_idx`. If the direct
  lookup also fails, report `child template detail unavailable`; do not infer a name or convert it into a data-readiness result.
- Authentication or API error: follow common authentication handling and report the server message.

## Recommended Chain

```text
PROJECT_ID_GATE → list_dashboard_templates → get_dashboard_template
→ every content cell's contents[].content_idx → get_content_template
```
