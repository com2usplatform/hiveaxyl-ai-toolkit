# list_content_templates (List Platform Content Templates)

Lists platform content templates for a confirmed company.

> **Prerequisite:** Follow PROJECT_ID_GATE in [`../SKILL.md`](../SKILL.md). This is a read tool.

## When to Use

- To browse reusable chart, ranking, funnel, and retention templates.
- To narrow candidates before requesting one detailed configuration.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `company_cd` | Y | Company code confirmed by PROJECT_ID_GATE |
| `lang` | N | Translation language. Default: `ko` |
| `content_type` | N | `chart`, `chart_rank`, `funnel`, or `retention` |
| `include_params` | N | Include every template's settings. Default: `false` |

## Return Value

Returns templates in platform display order with `template_idx`, translated name/description, content type,
chart type, and modification date. `params` is included only when requested.

## Decision Rules

- Supported content filters are `chart`, `chart_rank`, `funnel`, and `retention`.
- Keep `include_params=false` while browsing. Use `get_content_template` for selected templates; loading every params
  object can make the response unnecessarily large.
- Template IDs are not saved content IDs.

## On Failure

- Empty result with a type filter: retry without the filter before concluding that no templates exist.
- Authentication or API error: follow common authentication handling and report the server message.

## Recommended Chain

```text
PROJECT_ID_GATE → list_content_templates(include_params=false)
→ get_content_template(selected template_idx)
```
