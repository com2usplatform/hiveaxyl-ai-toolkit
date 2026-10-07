# preview_retention (Query Retention Data)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE are required.

## When to Use

- To query, by cohort, the share of users who came back with a return event (for example, a re-login) after a base event (for example, a new sign-up).
- Use it after first confirming event and filter information in the order `list_events` → `list_dimensions`.
- **Before calling, you must obtain `org_idx`/`workspace_idx` through ORG_WORKSPACE_GATE, starting with `check_analytics_admin`.**

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `project` | Y | List of project IDs. For example, `["com.example.game"]` |
| `date_params` | Y | Date range dict (see below) |
| `base_event` | Y | The cohort base event (see below) |
| `retention_event` | Y | The return event (same format as `base_event`, usually with `filters=[]`) |
| `company_cd` | Y | Company code. The `company_cd` from `list_projects` |
| `org_idx` | Y | Organization idx. Obtained through ORG_WORKSPACE_GATE |
| `workspace_idx` | Y | Workspace idx. Obtained through ORG_WORKSPACE_GATE |
| `identifier` | N | Cohort identifier: the name of a dimension present on both `base_event` and `retention_event`, such as `"userId"` or `"deviceId"` (default `"userId"`) |
| `chart_type` | N | `"table"`\|`"line"` (default `"table"`) |
| `dimensions` | N | Grouping basis (see below) |
| `adhoc_filters` | N | Global filters. The same three `filter_type` values as `preview_chart` (index/snapshot/segment) |
| `display_format` | N | `"percentage"`\|`"figure"` (default `"percentage"`) |
| `content_name` | N | Content name (default `"preview"`) |

### date_params structure

For a relative period, set `start_date_type`/`end_date_type` to `"V"` and pass an integer offset from today in
`start_value`/`end_value`. In that case, do not compute or pass `start_date`/`end_date`.

### base_event / retention_event structure

- Take the event ID and name from `list_events`, and take the filters' dimension ID, name, and data type from
  `list_dimensions`.
- For a new-user basis, `base_event` usually specifies something like `newUser="Y"` in `filters`.
- `retention_event` is usually left empty with `filters=[]`.

### dimensions structure

Each entry consists of the dimension ID and name confirmed from `list_dimensions`, plus a display alias.

## Return Value

Returns the Analytics query API response object, including the base user count and retention values per cohort.
The actual columns and display structure vary with the `chart_type`, `display_format`, and `dimensions` settings.

- An empty result does not mean the save succeeded or that event collection is complete.
- Use the ratios, figures, and display format the server returned exactly as given.

## Decision Rules

- Do not arbitrarily guess the `idx`/`event_name` of `base_event`/`retention_event` (NO_GUESSING).
- If you need filters or dimensions, confirm them first with `list_dimensions(company_cd, event_name)`.

## On Failure

- Empty result: check that `project` and the date range are correct.
- API error: the error message includes the server response. Read the message and fix the parameters.
- Organization or workspace authorization error: perform ORG_WORKSPACE_GATE again.

## Recommended Chain

```
list_projects → list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_retention
```
