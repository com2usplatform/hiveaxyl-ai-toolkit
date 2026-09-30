# list_dashboard_templates (List Platform Dashboard Templates)

Lists platform dashboard templates for a confirmed company.

> **Prerequisite:** Follow PROJECT_ID_GATE in [`../SKILL.md`](../SKILL.md). This is a read tool.

## When to Use

- As the always-available source for dashboard recommendations, regardless of confirmed genre or BM.
- To narrow platform candidates before loading their member content.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `company_cd` | Y | Company code confirmed by PROJECT_ID_GATE |
| `lang` | N | Translation language. Default: `ko` |

## Return Value

Returns `template_idx`, translated dashboard name/description, display order, global date/filter settings, and
modification date. Member content is not included.

## Decision Rules

This is the always-available recommendation source: genre and BM are not required. When genre/BM are unknown,
recommend multiple suitable platform templates using the confirmed purpose/persona, or otherwise their generality,
name, description, selected template details, and data readiness. Do not restrict the result to a summary template
solely because genre/BM are unknown.

- The list does not contain member content. Call `get_dashboard_template` only for selected candidates.
- A template is reference configuration, not an asset already created in the user's workspace.

## On Failure

- Empty result: report that no platform template was returned; do not fabricate one or substitute a catalog ID.
- Authentication or API error: follow common authentication handling and report the server message.

## Recommended Chain

```text
PROJECT_ID_GATE → list_dashboard_templates → get_dashboard_template(selected template_idx)
→ get_content_template for selected member content
```
