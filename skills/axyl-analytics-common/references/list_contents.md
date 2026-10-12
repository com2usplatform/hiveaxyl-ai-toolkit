# list_contents (List Saved Content)

List the content items (chart/funnel/retention) and dashboards **already saved** in an organization.
Used for the duplicate check before saving (DUPLICATE_GATE) and for finding existing assets
(EXISTING_ASSET_FIRST). Both paths start here, but they read the result differently: for
EXISTING_ASSET_FIRST a roughly matching asset in the confirmed project is good enough to answer with (stating any filter or
breakdown it applies), while DUPLICATE_GATE must
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
| `content_type` | N | `chart`/`chart_rank`/`funnel`/`retention`, or `대시보드` (or `dashboard`) for dashboards. Omit for everything |
| `name` | N | The name you are about to create. Compared with separators (spaces, commas, ...) ignored |
| `metrics` | N | **Only the metric measure names** of the content you are about to create (e.g. `["AU","PU"]`) |
| `mine_only` | N | `true` returns only items you registered |
| `limit` | N | Maximum rows returned (default 50; 0 or less returns every row) |

Passing `name` or `metrics` returns only duplicate candidates, each tagged with `match`. Omitting both returns
the rows that pass the other filters, newest first. **Either way, at most `limit` rows (default 50) are returned** —
`truncated=true` means more exist (the rules below say when to use `limit=0`).

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
- Start with the proposed `name` (and `metrics` for registered-metric-only content), then confirm those candidates in detail.
  This catches the most actionable duplicates cheaply.
- If no confirmed duplicate was found and the proposed content contains an event-based measure, or is a funnel or retention,
  run one widened query restricted to the target `workspace_idx` and `content_type`, omitting `name` and `metrics`. Inspect the
  bounded result (the default 50 newest rows) with `get_content`. Apply the same bounded widening to dashboards whose proposed
  members include any such content: inspect the returned dashboard rows with `get_dashboard`, then compare their members.
- If the widened result is truncated, do **not** automatically call with `limit=0`. State how many same-type rows exist and
  that older renamed copies were not exhaustively checked; include this limitation with WRITE_APPROVAL. Use `limit=0` only
  when the user explicitly asks for an exhaustive duplicate audit, or on an exact-name/type recovery query when resolving
  whether an uncertain previous write succeeded before any retry. Never use `mine_only` in DUPLICATE_GATE — it hides other
  people's duplicates. Use `matched` for the widened same-type count; `total` is the organization-wide count before filters.
- `matched` of 0 proves there is no duplicate only when `name`/`metrics` can represent the proposed composition. For a
  truncated widened event/funnel/retention/dashboard check, report "none in the checked candidates," not "none exists."
- `truncated=true` means older candidates exist. Do not conclude "none found" or silently expand to an unbounded response.
- Show the user the content name and `url`, not the `idx`.

## On Failure

- Too many results or `truncated=true`: narrow by workspace, content type, or name. For DUPLICATE_GATE, never narrow by
  ownership. Keep the widened pass bounded and disclose incomplete coverage; use `limit=0` only for an explicitly requested
  exhaustive audit or an exact-name/type uncertain-write recovery check.
- Unknown asset type: do not choose a detail endpoint; report the unsupported type.
- Organization or workspace authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- API error: report the server message and do not infer whether a duplicate exists.

## Recommended Chain

```text
ORG_WORKSPACE_GATE → list_contents(target workspace, proposed name/metrics)
→ if needed, one bounded widened list by target content_type with no name/metrics
→ get_content or get_dashboard for the returned candidates
→ compare full configuration → WRITE_APPROVAL when creation should continue
```
