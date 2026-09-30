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

Treat it as "the same content" only when **all** of the following match.

1. `content_type` + `chart_type`
2. `project`
3. The measure composition in `params` (both metric- and event-based), `dimensions`, `adhoc_filters`
4. `params.date_params` — **branch on `start_date_type`/`end_date_type` first.**
   - `"V"` (relative): compare `start_value`/`end_value`. `start_date`/`end_date` are resolved at save time,
     so identical settings still show different dates — do not compare them.
   - `"F"` (fixed): the explicit `start_date`/`end_date` **are** the setting, so compare those.
     `start_value`/`end_value` come back as 0 and mean nothing here.
   A `"V"` content and an `"F"` content are never duplicates of each other, even if the dates happen to line up.

- If any one differs, it is not a duplicate. State in one line what differs and proceed.
- `params` uses the console's storage format, which differs from the argument format of
  `preview_chart`/`create_chart` — the conversion rules are the same as described in the `get_content_template`
  tool docstring. Unlike templates, the event and metric idx values belong to the same company, so they do not
  need to be looked up again.

## On Failure

- Missing candidate or wrong asset kind: return to `list_contents` and select a row with `kind="content"`.
- Workspace mismatch or permission error: repeat ORG_WORKSPACE_GATE for the candidate's workspace.
- Empty or malformed detail: report that exact comparison is unavailable; do not declare a duplicate from the list row.

## Recommended Chain

```text
ORG_WORKSPACE_GATE → list_contents → get_content(candidate content_idx)
→ compare full params → reuse, skip, or continue to creation
```
