# list_contents (List Saved Content)

List the content items (chart/funnel/retention) and dashboards **already saved** in an organization.
Used for the duplicate check before saving (DUPLICATE_GATE) and for finding existing assets
(EXISTING_ASSET_FIRST). Both paths start here, but they read the result differently: for
EXISTING_ASSET_FIRST a roughly matching asset is good enough to answer with, while DUPLICATE_GATE must
confirm an exact match before it declines to create anything.

> **Prerequisite:** Follow PROJECT_ID_GATE and ORG_WORKSPACE_GATE in [`../SKILL.md`](../SKILL.md).

## When to Use

- Immediately **before** calling `create_chart`/`create_chart_rank`/`create_funnel`/`create_retention`/`create_dashboard`.
- When the user looks for an existing asset ("do we have a chart like this?").
- When deciding whether to build new content for a dashboard or reuse existing content.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed with `list_projects` |
| `org_idx` | Y | Organization idx confirmed by ORG_WORKSPACE_GATE |
| `workspace_idx` | N | Restricts the result to one workspace. **Pass the target workspace** — duplication is judged per workspace |
| `content_type` | N | `chart`/`chart_rank`/`funnel`/`retention`/`대시보드` (the dashboard filter value is this literal Korean string). Omit for everything |
| `name` | N | The name you are about to create. Compared with separators (spaces, commas, ...) ignored |
| `metrics` | N | **Only the metric measure names** of the content you are about to create (e.g. `["AU","PU"]`) |
| `mine_only` | N | `true` returns only items you registered |
| `limit` | N | Maximum rows returned (default 50) |

Passing `name` or `metrics` returns only duplicate candidates, each tagged with `match`. Omitting both returns
the whole list, newest first.

## Return Value

Returns total and matched counts, truncation status, and candidate rows. Each row identifies its asset kind, type,
name, metric summary, workspace, registration metadata, URL, and optional `match` grade.

| `match` | Meaning |
|---|---|
| `exact` | Same name, and the metrics match or cannot be compared. Most likely a duplicate |
| `name` | Same name but the metric composition looks different (only when both sides are comparable) |
| `metrics` | Only the metric composition matches. May be a copy that was renamed |
| `partial` | The name partially matches |

- `kind` decides which detail tool to call — `content` → `get_content`, `dashboard` → `get_dashboard`.
  Content and dashboards use **separate `idx` sequences**, so never mix them.
- `metrics_comparable=false` means the item was built only from events, or it is a funnel/retention, so it
  **cannot be compared by metrics**. The candidate was matched by name alone, which makes the detail check
  more important, not less.

## Decision Rules

- **Never tell the user "it already exists" from `match` alone.** The list carries no `params` or `chart_type`.
  Put the candidate `idx` into `get_content`/`get_dashboard`, compare `params`, and only then answer.
- Do not rule out a duplicate because the metrics differ (`metrics` holds metric measures only).
- If there are too many candidates, narrow in this order: `workspace_idx` → `content_type` → `mine_only`.
- `matched` of 0 means there is no duplicate. Proceed with the save.
- `truncated=true` means more candidates exist. Do not conclude "none found".
- Show the user the content name and `url`, not the `idx` (Common Display Rules).

## On Failure

- Too many results or `truncated=true`: narrow by workspace, content type, ownership, or name.
- Unknown asset type: do not choose a detail endpoint; report the unsupported type.
- Permission error: repeat the applicable organization/workspace gate.
- API error: report the server message and do not infer whether a duplicate exists.

## Recommended Chain

```text
ORG_WORKSPACE_GATE → list_contents(target workspace, proposed name)
→ get_content or get_dashboard for each plausible candidate
→ compare full configuration → WRITE_APPROVAL when creation should continue
```
