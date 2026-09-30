# preview_funnel (Query Funnel Data)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + ORG_WORKSPACE_GATE are required.

## When to Use

- To query conversion rates between several event steps (for example, sign-up → tutorial complete → first payment).
- Use it after first confirming event and filter information in the order `list_events` → `list_dimensions`.
- **Before calling, you must obtain `org_idx`/`workspace_idx` through ORG_WORKSPACE_GATE, starting with `check_analytics_admin`.**

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `project` | Y | List of project IDs. For example, `["com.example.game"]` |
| `date_params` | Y | Date range dict (see below) |
| `sections` | Y | List of funnel steps. Two or more (see below) |
| `company_cd` | Y | Company code. The `company_cd` from `list_projects` |
| `org_idx` | Y | Organization idx. Obtained through ORG_WORKSPACE_GATE |
| `workspace_idx` | Y | Workspace idx. Obtained through ORG_WORKSPACE_GATE |
| `chart_type` | N | `"table"`\|`"column"`\|`"line"`\|`"funnel"` (default `"table"`) |
| `compare_type` | N | `"prev"` (versus the previous step) \| `"first"` (versus the first step) (default `"prev"`) |
| `standard_days` | N | Base period in days (default `1`) |
| `tracking_days` | N | Tracking period in days. Counts a conversion only if the next step occurs within this window (default `1`) |
| `convert_type` | N | `"y"`\|`"n"`. `"y"` includes step-1 conversions in the steps after step 1 as well (default `"y"`) |
| `user_display_type` | N | `"percent"`\|`"count"` (default `"percent"`) |
| `content_name` | N | Content name (default `"preview"`) |

### date_params structure

- `start_date`/`end_date` use the `YYYY-MM-DD` format (unlike preview_chart — no hours, minutes, or seconds).
- `start_date_type`/`end_date_type`: `"ep"` = a fixed date (explicit period).
- For a relative period, set `start_date_type`/`end_date_type` to `"V"` and pass an integer offset from today in
  `start_value`/`end_value`. In that case, do not compute or pass `start_date`/`end_date`.

### sections structure

- Each step specifies the display title, the event ID and name confirmed from `list_events`, the aggregation basis
  `identifier`, and optional filters.
- `table_description`: if omitted, `event_name` is used.
- `table_type`: `"hive"` (default) \| `"adjust"` \| `"appsflyer"`.
- Choose `identifier` from that event's `list_dimensions` result; using the same basis across all steps is recommended.
- The dimension ID, name, and data type in `filters` also come from the `list_dimensions` result.

## Return Value

Returns the Analytics query API response object, including the user count and conversion rate for each funnel step.
The actual columns and display structure vary with the `chart_type`, `compare_type`, and `user_display_type` settings.

- An empty result does not mean the content is ready to save; it means no data was computed under the current conditions.
- Do not recompute the return value yourself — use the figures and display values the server provided.

## Decision Rules

- `sections` is meaningful only with at least two steps.
- Do not arbitrarily guess `event_idx`/`event_name`. Always take them from the `list_events()` result (NO_GUESSING).
- If you need filters, first confirm `dimension_idx`/`dimension_name`/`dimension_data_type` with `list_dimensions(company_cd, event_name)`.

## On Failure

- Empty result: check that `project` and the date range are correct.
- API error: the error message includes the server response. Read the message and fix the parameters.
- Organization or workspace authorization error: perform ORG_WORKSPACE_GATE again.

## Recommended Chain

```
list_projects → list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_funnel
```
