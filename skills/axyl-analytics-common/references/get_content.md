# get_content (Get Saved Content Detail)

Retrieve the full settings of one saved content item. This is the tool that **confirms** whether a candidate
found by `list_contents` really is the same content.

> **Prerequisite:** Take `content_idx` from a `list_contents` row with `kind="content"`, or from
> `get_dashboard`'s `contents[].content_idx` (NO_GUESSING).

## When to Use

- In DUPLICATE_GATE, to compare a candidate's period, dimensions, filters, and chart type.
- When building similar content based on an existing item.
- When checking which metrics a dashboard's member content was built from.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed with `list_projects` |
| `org_idx` | Y | Organization idx confirmed through the organization gate |
| `workspace_idx` | Y | Workspace idx from the candidate row; the server verifies membership and ownership |
| `content_idx` | Y | Content idx. For dashboards use `get_dashboard`, not this tool |
| `include_grid_config` | N | `true` includes the raw table display state. Default returns the summary (`params.grid_config_summary`) |

## Return Value

Returns content identity and type, workspace/project scope, permission, full `params`, dashboard association, and
the Analytics console URL.

- `chart_type`, `project`, and `params` are **not in the list response**. Confirm duplicates with these three.
- A different `project` means the content looks at a **different app**, so it is not a duplicate even with the
  same name.
- A non-zero `dashboard_idx` means the content was created for one specific dashboard.
- Measures built from events live in `params.measure[].expressions[].tokens` as `type=event`/`event_detail`.
  They never appear in the list's `metrics`, so **this is the only place to check them.** For funnels and
  retentions, check `params.sections` / `base_event`·`retention_event`.

## Decision Rules

Treat it as "the same content" only when **all** of the following semantic settings match. Compare the stored
`params` structure rather than only the preview arguments; ignore only server-derived or transient fields explicitly
excluded below.

1. `content_type` + `chart_type`
2. `project`
3. The complete measure composition in `params` (metric and event tokens, formulas, per-term periods, per-term `filters`, grouping formulas,
   aliases), plus `dimensions` and `adhoc_filters`
4. Type-specific settings:
   - `chart`: table display semantics such as pivots, row groups, per-column aggregation, and hidden columns. For a table,
     call with `include_grid_config=true` when the summary does not prove an exact match.
   - `chart_rank`: the chart settings above plus `rank_limit`, `rank_order`, `rank_tie_mode`, and `rank_group_mode`.
   - `funnel`: `sections`, `compare_type`, `standard_days`, `tracking_days`, `convert_type`, and `user_display_type`.
   - `retention`: `base_event`, `retention_event`, the identifier (stored as `conditions[].base_dimension`/`retention_dimension`),
     `dimensions`, and `display_format`.
5. `params.date_params`, including `period` and `minute_interval` when present — **branch on
   `start_date_type`/`end_date_type` first.**
   - `"V"` (relative): compare `period`, `start_period`/`end_period`, and `start_value`/`end_value`.
     `start_date`/`end_date` are resolved at save time,
     so identical settings still show different dates — do not compare them.
   - `"F"` (fixed): the explicit `start_date`/`end_date` **are** the setting, so compare those.
     `start_value`/`end_value` come back as 0 and mean nothing here.
   Funnel `"ep"` is fixed and is compared like `"F"`. A relative content and a fixed content are never duplicates,
   even if their resolved dates happen to line up.

- If any one differs, it is not a duplicate. State in one line what differs and proceed.
- `params` uses the console's storage format, which differs from the argument format of
  `preview_chart`/`create_chart` — the conversion rules are the same as described in the `get_content_template`
  tool docstring. Unlike templates, the event and metric idx values belong to the same company, so they do not
  need to be looked up again. Do not use them for another company's project.

## On Failure

- Missing candidate or wrong asset kind: return to `list_contents` and select a row with `kind="content"`.
- Pass the workspace from the candidate's `list_contents` row. If you passed a different one, run ORG_WORKSPACE_GATE for
  the row's workspace and call again.
- Organization or workspace authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- Empty or malformed detail: report that exact comparison is unavailable; do not declare a duplicate from the list row.

## Recommended Chain

```text
ORG_WORKSPACE_GATE → list_contents → get_content(candidate content_idx)
→ compare full params → reuse, skip, or continue to creation
```
