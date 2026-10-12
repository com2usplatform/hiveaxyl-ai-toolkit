---
name: axyl-create-content
metadata:
  version: "1.0.0"
description: |
  Creates and saves Hive Analytics chart, ranking, funnel, or retention content, and can assemble approved content
  into a dashboard. Follow axyl-analytics-common first.

  TRIGGER when:
  - The user asks to build and save a chart, ranking, funnel, or retention
  - The user asks to create a dashboard with an already finalized composition
  - The user asks to bundle specified metrics or charts into one dashboard
  - The user asks to recreate an existing dashboard or a dashboard template in another project or workspace of the same company

  DO NOT TRIGGER when:
  - The dashboard composition is undecided or needs recommendation/readiness assessment → axyl-design-dashboard
  - The request is read-only analysis → axyl-analytics-common, axyl-detect-anomaly, or axyl-drill-down-metrics
  - The request creates a user segment or snapshot → axyl-create-segment
  - The request is development work unrelated to analytics
---

# axyl-create-content

> **CRITICAL — Always review the common rules in [axyl-analytics-common](../axyl-analytics-common/SKILL.md) first.**
> **CRITICAL — Saving (`create_*`) and dashboards (`create_dashboard`) are write operations. Never run them without WRITE_APPROVAL.**
> **CRITICAL — Check for duplicates with `list_contents` before saving (DUPLICATE_GATE). The console will save any number of items with the same name.**
> **CRITICAL — Use only verified values for `content_idx`, `project_id`, and `org_idx`/`workspace_idx` (NO_GUESSING).**
> **CRITICAL — Before building each content item, read its `create_*` reference and the corresponding `preview_*` reference first.**
> **CRITICAL — Ranking is supported as the first-class `chart_rank` content type, not as a `chart` workaround. Verify with `preview_chart_rank` and save with `create_chart_rank`.**
> **CRITICAL — Pick up a request handed over from design-dashboard only when it carries a `design_approval.approved=true` context in which the user approved the final composition at the result review. Without it, return to design-dashboard's DESIGN_APPROVAL_GATE and do not start a preview or a save.**

---

## Tools

- **Save (write):** `create_chart` / `create_chart_rank` / `create_funnel` / `create_retention`
  → [create_chart.md](../axyl-analytics-common/references/create_chart.md) · [create_chart_rank.md](../axyl-analytics-common/references/create_chart_rank.md) · [create_funnel.md](../axyl-analytics-common/references/create_funnel.md) · [create_retention.md](../axyl-analytics-common/references/create_retention.md)
- **Assemble (write):** `create_dashboard`
  → [create_dashboard.md](../axyl-analytics-common/references/create_dashboard.md)
- **Update (write):** `update_chart` / `update_chart_rank` / `update_funnel` / `update_retention` / `update_dashboard`
  → [update_chart.md](../axyl-analytics-common/references/update_chart.md) · [update_chart_rank.md](../axyl-analytics-common/references/update_chart_rank.md) · [update_funnel.md](../axyl-analytics-common/references/update_funnel.md) · [update_retention.md](../axyl-analytics-common/references/update_retention.md) · [update_dashboard.md](../axyl-analytics-common/references/update_dashboard.md)
  Use these to fix content or dashboards that already exist. **Consider updating before creating anything new** — piling up copies makes it impossible to tell which one is current.
- **Verify (read):** `preview_chart` / `preview_chart_rank` / `preview_funnel` / `preview_retention`
  → [preview_chart.md](../axyl-analytics-common/references/preview_chart.md) · [preview_chart_rank.md](../axyl-analytics-common/references/preview_chart_rank.md) · [preview_funnel.md](../axyl-analytics-common/references/preview_funnel.md) · [preview_retention.md](../axyl-analytics-common/references/preview_retention.md)
- **Duplicate check (read):** `list_contents` / `get_content` / `get_dashboard`
  → [list_contents.md](../axyl-analytics-common/references/list_contents.md) · [get_content.md](../axyl-analytics-common/references/get_content.md) · [get_dashboard.md](../axyl-analytics-common/references/get_dashboard.md)
- **Template source (read):** `get_dashboard_template` / `get_content_template` — when recreating from a platform template
  → [get_dashboard_template.md](../axyl-analytics-common/references/get_dashboard_template.md) · [get_content_template.md](../axyl-analytics-common/references/get_content_template.md)
- **Metric registration (write, a preceding step):** `create_metric` — only in the cases listed in its "When to Use" (including a metric that cannot be expressed through content arguments, or an explicit request to register one)
  → [create_metric.md](../axyl-analytics-common/references/create_metric.md)

### Metrics That Cannot Be Expressed Through Content Arguments

- **A metric whose terms have different periods (stickiness = DAU / MAU, and so on)** cannot be built from chart arguments.
  `measure_date`, which fixes a period per term, exists only in a metric definition, so register it first with `create_metric`
  and build the content from that `metric_idx`. This needs **two approvals** — metric registration and content saving are each subject to WRITE_APPROVAL.
- **A metric needing a first aggregation by time unit plus a second aggregation, such as peak concurrent users**, can be built
  directly from chart arguments (`group_formular`/`group_format`/`group_interval` — the "Two-stage aggregation" section of
  [preview_chart.md](../axyl-analytics-common/references/preview_chart.md)). Register it as a metric only in the cases `create_metric`'s "When to Use" lists (for example, reuse across several content items or an explicit request to register it).

## Reference Documents

- [Layout policy](references/layout_policy.md) — automatic placement rules on the 24-column grid
- [Request decomposition patterns](references/dashboard_patterns.md) — examples of decomposing a natural-language request into a content list
- [Template conversion](references/template_mapping.md) — converting platform template params into `create_*` arguments

---

## Workflow

### Prerequisite — Review the common rules

PROJECT_ID_GATE, ORG_WORKSPACE_GATE, SCHEMA_FIRST, DUPLICATE_GATE, WRITE_APPROVAL,
POST_WRITE_LINK, and NO_GUESSING from axyl-analytics-common all apply.

### Phase 0 — Decompose the request

```
Step 0-1. Is there a follow-up context handed over by design-dashboard?
  ├─ YES + design_approval.approved=true
  │     → do not decompose. Use the display order, names, types, and chart_type from contents[] as given
  │        (handoff format: axyl-design-dashboard/references/handoffs.md)
  ├─ YES + no approval → return to design-dashboard for the result review and composition approval ⛔
  └─ NO                → Step 0-1b

Step 0-1b. Is the composition decided?
  ├─ YES — the user named the metrics or charts to include, or asked for a single content item → Step 0-2
  ├─ YES — the user asked to recreate an existing dashboard or template → "Recreating an Existing Dashboard" below
  └─ NO  — only a theme such as "make me a revenue dashboard" → hand over to axyl-design-dashboard for
           recommendation, readiness diagnosis, and composition approval. Do not decompose it here ⛔

Step 0-2. Decompose the request into a content list. Each content item = a type (chart/chart_rank/funnel/retention) + a metric or condition.
  - Dashboard request      → several content items + a dashboard name
  - Single content request → one content item (skip dashboard assembly)
```
For decomposition examples, see [references/dashboard_patterns.md](references/dashboard_patterns.md).

**When you have received a follow-up context, do not reinterpret the composition.** The names, types, metrics, filters, and periods
are values already agreed with the user and checked for readiness. Decomposing again would diverge from the composition the user
approved. If you see a reason to change something, do not change it on your own — confirm with the user. Any handed-over `excluded[]`
is not an implementation target, so leave it out and state in the result what you left out.

### Recreating an Existing Dashboard

When the user asks to make an existing dashboard (or a dashboard template) again in another project or workspace **of the
same company**. Recreating a dashboard in another company's project is not supported — the events, metrics, and properties
belong to each company, so tell the user and stop.

1. Read the source: `get_dashboard`, then `get_content` for each content item. For a platform dashboard template, use
   `get_dashboard_template` and `get_content_template`, and convert per [template_mapping.md](references/template_mapping.md).
2. Run Phase 1 for the **target** project and workspace, and confirm it belongs to the source's company (`company_cd`).
   The source's events and metrics are then used as they are; confirm in the target with the Phase 2 preview that they
   have data. When the target project differs from the source, also check each filter value (global, chart, and per-term)
   against the target with `query_adhoc`, as in the template filter check; a value that does not exist there matches nothing.
3. Build each content item through Phase 2 (preview in the target, duplicate check, approval, save).
4. Assemble in Phase 3 in the source order with each item's `width`/`height`/`memo`/`row`, and carry the global period and filters
   after the check in the `create_dashboard` reference. Text and image panels cannot be recreated; tell the user to add
   them in the console.

### Phase 1 — Gates (axyl-analytics-common)

```
Step 1-1. PROJECT_ID_GATE       → confirm project / company_cd
Step 1-2. ORG_WORKSPACE_GATE    → confirm org_idx / workspace_idx
Step 1-3. SCHEMA_FIRST          → confirm the events, dimensions, and metrics each content item needs
                                  (list_metrics → list_events/list_dimensions)
Step 1-4. DUPLICATE_GATE        → for each proposed content/dashboard, query by its name
                                  (and metric names for registered-metric-only content)
                                  → confirm the returned candidates in detail; do not preload the whole workspace
Step 1-5. For a dashboard request, call get_dashboard, then get_content for every content member and compare the full
          member compositions and dashboard-level settings before any child content is written
          → if no duplicate was confirmed among the name candidates and any proposed member is event-based, a funnel, or a retention,
            run one bounded widened dashboard query without name/metrics and inspect the returned dashboard rows
          ├─ identical composition → have the user choose: use the existing one / create a copy / skip ⛔
          └─ partial overlap       → state the differences and let the user choose: add the missing content to the
                                     existing dashboard (update_dashboard; offer only when its permission is EDITOR) /
                                     create a new one / skip ⛔
          └─ different             → state in one line what differs and proceed (DUPLICATE_GATE)
```

**If the handed-over context has verified values, do not redo Steps 1-1 through 1-3.** `company_cd`, `project`,
`org_idx`, `workspace_idx`, and `metric_idx`/`event_idx`/`dimension_idx` are values design-dashboard confirmed against
the target company's schema, so use them as is — re-querying only repeats the same request and risks newly selecting a
different metric with a similar name.
By contrast, **always perform Steps 1-4 and 1-5 (DUPLICATE_GATE) even with a handed-over context** — the same content may have
been created between design time and save time, and design-dashboard cannot know the state just before the save.

Do not preload the entire workspace. Reuse an identical candidate query when several proposed items share it; otherwise keep
the initial name/metrics queries narrow. When event-based content, funnels, or retentions need a renamed-copy check, widen at
most once per target workspace and `content_type` with the default bounded result and reuse it for every proposed item of
that type; rerun it after a workspace change or a failed or uncertain write. If it is
`truncated`, disclose that older renamed copies were not exhaustively checked and include that limitation with WRITE_APPROVAL.
Use `limit=0` only when the user explicitly asks for an exhaustive audit or on an exact-name/type recovery query when checking
whether an uncertain previous write succeeded before a retry. Never use `mine_only` in DUPLICATE_GATE.

If Step 1-5 leads the user to choose using the existing dashboard or skipping, stop without previewing or saving any content.
Proceed to Phase 2 when they choose to create a copy or to add missing content to the existing dashboard (then finish with
`update_dashboard` in Phase 3 instead of `create_dashboard`), and compose each child item from the user's choice of reusing the
existing content, creating a copy, or skipping.

### Phase 2 — Build each content item (repeat per item)

```
Step 2-0. If the handed-over context has a platform template reference, convert get_content_template's params
          into create_* arguments → [template_mapping.md](references/template_mapping.md)
Step 2-1. Preview the data with preview_<type> → have the user confirm it
          └─ if the result is empty, recheck the project, period, and configuration once, then show a "currently no data" warning with the evidence
Step 2-2. [DUPLICATE_GATE] Select candidates from the Step 1-4 query results
          ├─ registered-metric-only content → rows with the same name or metric
          └─ any event-based measure, funnel, or retention → if the narrow candidates contained no duplicate,
                                                              use the returned rows from one bounded same-type widening
          ├─ no candidate → Step 2-3
          └─ candidate    → compare params with get_content(company_cd, org_idx, workspace_idx, candidate idx)
                        ├─ same      → have the user choose: reuse the existing asset / create a copy / skip ⛔
                        └─ different → state in one line what differs, then Step 2-3
Step 2-3. [WRITE_APPROVAL] Wait for explicit approval to save ⛔
          └─ if the result is empty, state in the approval text that no data will be visible even after saving
Step 2-4. Call create_<type> → collect content_idx
```

> With several content items, you may gather the preview results and duplicate-check results and present them at once for a
> **batch approval**. Never call `create_*` without approval.

**Cautions when judging duplicates**

- Do not answer "it already exists" from `match` alone. The list carries no `params` or `chart_type`, so confirm by
  comparing `params` from `get_content`.
- Do not rule out a duplicate just because the metrics look different — `metrics` holds only measures built from registered
  metrics, and measures built from events, along with the events of funnels and retentions, do not appear (`metrics_comparable=false`).
  A renamed event-based copy therefore cannot be caught by name or metrics. If the narrow candidates contain no duplicate, compare
  the bounded widened same-type result with `get_content`. When it is truncated, report the unchecked older range rather
  than automatically loading every row.
- For period comparison, look first at `date_params`'s `start_date_type`/`end_date_type`.
  For `"V"` (relative), compare `period`, `start_period`/`end_period`, and `start_value`/`end_value` — do not compare `start_date`/`end_date` here, because they are computed
  at save time and the same configuration will show different dates.
  For `"F"` (fixed), the reverse holds: `start_date`/`end_date` are the configuration itself, so compare those
  (there, `start_value`/`end_value` come back as 0 and are meaningless).
  `"V"` and `"F"` are never duplicates of each other, even when the dates happen to coincide.
  Funnels write a fixed period as `"ep"` instead of `"F"` — treat `"ep"` as fixed, and build funnel
  `date_params` with `"ep"` (see [preview_funnel.md](../axyl-analytics-common/references/preview_funnel.md)).
- Even for a duplicate, create it if the user says to. The gate **informs**; it does not block.
- Reuse is possible only for existing content in the target workspace with verified access. If reuse is chosen, put the existing
  `content_idx` into the assembly list and do not call `create_<type>`.
- Save approval for an empty preview counts as WRITE_APPROVAL only when the warned content and the final save composition were
  presented together. Without approval, skip that content item.

### Phase 3 — Assemble the dashboard (optional)

```
One content item & no dashboard needed → return the content url built in Phase 2 and stop
Dashboard request                      → create_dashboard(contents=[the content_idx values confirmed in Phase 2, in display order],
                                                           date_params/adhoc_filters when requested or carried from a
                                                           template/handoff)
                                          → return the dashboard url
```

Judge dashboard duplicates by the dashboard copy criteria in axyl-analytics-common DUPLICATE_GATE.
To add content to an existing dashboard, read it with `get_dashboard` and confirm its `permission` is `EDITOR` before saving any
content for it (otherwise offer a copy or a request to the author), then pass the full new list to `update_dashboard`
after WRITE_APPROVAL, carrying over each existing item's `width`/`height`/`memo`/`row` and passing text and image panels as
`{"panel_ref": n}` so the current layout is kept (a panel left out is not deleted; it moves to the bottom).
Create a new dashboard only after showing the final composition and target workspace and obtaining WRITE_APPROVAL.
When the request, a template, or a design handoff includes a dashboard-wide period or filters, pass them to
`create_dashboard` as `date_params`/`adhoc_filters` and show the exact settings in the same WRITE_APPROVAL. Check settings
from a template or handoff first, as the `create_dashboard` reference says (dimension, values, and a fixed period).
A period or filter the request states for the dashboard as a whole goes into these global settings; member content keeps
its own default period unless the user gives one per content. When the dashboard has a global period or filters, say in the
WRITE_APPROVAL summary that the Phase 2 previews used each member's own period and settings, and that the dashboard applies
the global ones, so its values can differ from the previews.

For a new layout the tool computes placement from the contents order, so **decide the order**. To keep an existing layout — a
template, a dashboard you are recreating, or an `update_dashboard` call that changes `contents` — also pass each item's `width`/`height`/`memo`/`row`,
and for `update_dashboard` the text and image panels by `panel_ref` (see [layout_policy.md](references/layout_policy.md)).

### Phase 4 — POST_WRITE_LINK

- Return the console link the tool returned: `url` from `create_*`/`create_dashboard`, `console_url` from `update_*`.

---

## Full Chain

```
[Decompose the request]
(PROJECT_ID_GATE) (ORG_WORKSPACE_GATE) (SCHEMA_FIRST)
Dashboard request: [DUPLICATE_GATE: get_dashboard + get_content for every content member before any child write]
  └─ use existing / skip → stop without creating child content
Per content item: preview_<type> → [duplicate check: get_content] → [WRITE_APPROVAL] → create_<type> → content_idx
  ├─ single & no dashboard needed → return the content url
  └─ dashboard request            → new: [WRITE_APPROVAL for the final assembly] → create_dashboard
                                    → existing dashboard change: [WRITE_APPROVAL] → update_dashboard
                                    → return the dashboard url
```

---

## Prohibited Behavior ❌

| Situation | Prohibited behavior | Correct behavior |
|------|----------|-----------|
| Before approval | Calling `create_*` right away | Verify with `preview_<type>`, then WRITE_APPROVAL |
| Duplicate unchecked | Saving without checking existing content | Find candidates with `list_contents` → confirm with `get_content` |
| Duplicate candidate found | Declaring "it already exists" from `match` alone | Compare in detail, then ask the user to reuse, copy, or skip |
| Metrics look empty | Concluding it is not a duplicate | It is event-based and so absent from the list — confirm with `get_content` |
| Dashboard duplicate | Comparing by the member `content_idx` set | Follow the dashboard copy criteria in axyl-analytics-common DUPLICATE_GATE (a copy has different idx values) |
| content_idx | Guessing or inventing it | Use only a `create_*` return value, or an existing idx confirmed to be in the same workspace with `get_content` |
| org_idx/workspace_idx unconfirmed | Calling with an arbitrary value (for example, 0) | Perform ORG_WORKSPACE_GATE, then retry |
| Metric or event unclear | Guessing and passing it | Confirm with list_metrics/list_events/list_dimensions |
| Saved but no link returned | Just stopping | Return the url per POST_WRITE_LINK |

---

## Exception Handling

| Situation | Response |
|------|------|
| Empty preview result | Recheck the project, period, and configuration once and warn. Save if the user explicitly approves creating empty content |
| Duplicate content found | Present the existing URL and the differences, and have the user choose to reuse, copy, or skip |
| Too many `list_contents` candidates | Narrow with `workspace_idx`, name, and `content_type`. Do not use `mine_only` for a duplicate check; keep the widened pass bounded and disclose the unchecked older range |
| `list_contents` `truncated=true` | Do not conclude "no duplicate" or automatically use `limit=0`; disclose incomplete coverage. Use `limit=0` only for an explicitly requested exhaustive audit or exact-name/type uncertain-write recovery |
| `create_*` failed | First check with DUPLICATE_GATE's recovery query whether it was created anyway — the first request may have succeeded. Count it as created only when an item that was not among the candidates seen before the save matches the approved settings; an existing same-name item does not count. If it was, do not save again. If not, retry only after fresh WRITE_APPROVAL (fix the parameters first if the error requires it, and say what changed or that nothing did). Stop if it is before dashboard assembly |
| Some content failed during dashboard assembly | Ask the user whether to proceed with only the successful `content_idx` values |
| Organization or workspace authorization denial | Do not retry the same call unchanged or with a guessed identifier; follow MCP_ACCESS_GATE (denied call with `org_idx`) |
| Not connected to the Hive Axyl MCP server (first install, never signed in), or the sign-in session expired | Apply MCP_CONNECTION_GATE in axyl-analytics-common. Cannot retry without user action |
