# create_chart_rank (Save Ranked Content)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE +
> ORG_WORKSPACE_GATE + DUPLICATE_GATE + **WRITE_APPROVAL** are required.

## When to Use

- Use this to save a ranking query result as content or to include it in a dashboard.
- Before saving, call `preview_chart_rank` with the same configuration and present the final name, configuration, and target workspace.

## Parameters

The query-related arguments follow `preview_chart_rank` exactly. The creation-only arguments are as follows.

| Parameter | Required | Description |
|---|---|---|
| `content_name` | N | Name of the content to save. Default `"rank"` |
| `content_description` | N | Content description. Default: empty string |

- `org_idx` is used only for authorization and is not included in the save body.
- Even when the preview is empty, the content can be saved if the user explicitly approves it along with the warning that no data will currently be displayed.

## Return Value

Returns the saved content ID, its type (`chart_rank`), its name, and the Analytics console URL.

- `content_idx` can be passed straight to `create_dashboard.contents`.
- The default layout size is 24×6 for a table and 12×4 for other charts.
- Return `url` to the user per POST_WRITE_LINK.

## Decision Rules

- Run `preview_chart_rank` first with the same configuration.
- After DUPLICATE_GATE, show what will be saved and whether the result is empty, then obtain WRITE_APPROVAL.
- Pass only the `content_idx` from the save result to `create_dashboard` in the same workspace.

## On Failure

- Ranking or dimension validation error: fix the `preview_chart_rank` configuration and preview again.
- Authorization error: perform ORG_WORKSPACE_GATE again.
- Save API error: do not retry automatically — to avoid creating a duplicate, check with `list_contents` whether it was created.

## Recommended Chain

```
(PROJECT_ID_GATE) → (SCHEMA_FIRST) → (ORG_WORKSPACE_GATE)
→ preview_chart_rank → (DUPLICATE_GATE) → [WRITE_APPROVAL] → create_chart_rank
```
