---
name: axyl-create-content
metadata:
  version: "1.0.0"
description: |
  Turns a natural-language request into chart, ranking, funnel, or retention content, saves it, and assembles several
  content items into a dashboard. Saving a single content item with no dashboard is also this skill's job.

  TRIGGER when:
  - The user asks to build and save a chart, ranking, funnel, or retention
  - The user asks to create a dashboard whose composition is already finalized
  - The user asks to bundle several metrics or charts into one dashboard

  DO NOT TRIGGER when:
  - The composition is undecided — as in "make me a dashboard" — or recommendations by purpose, persona, genre, and BM
    with a data-readiness assessment are needed first → axyl-design-dashboard
  - Data is only being queried or analyzed, not saved → preview_chart or axyl-drill-down-metrics
  - The request is to create and save a segment (a user set) or take a snapshot → axyl-create-segment
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
- **Metric registration (write, a preceding step):** `create_metric` — only when creating a metric that cannot be expressed through content arguments
  → [create_metric.md](../axyl-analytics-common/references/create_metric.md)

### Metrics That Cannot Be Expressed Through Content Arguments

- **A metric whose terms have different periods (stickiness = DAU / MAU, and so on)** cannot be built from chart arguments.
  `measure_date`, which fixes a period per term, exists only in a metric definition, so register it first with `create_metric`
  and build the content from that `metric_idx`. This needs **two approvals** — metric registration and content saving are each subject to WRITE_APPROVAL.
- **A metric needing a first aggregation by time unit plus a second aggregation, such as peak concurrent users**, can be built
  directly from chart arguments (`group_formular`/`group_format`/`group_interval` — the "Two-stage aggregation" section of
  [preview_chart.md](../axyl-analytics-common/references/preview_chart.md)). Register it as a metric only when it will be reused across several content items.

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

### Phase 1 — Gates (axyl-analytics-common)

```
Step 1-1. PROJECT_ID_GATE       → confirm project / company_cd
Step 1-2. ORG_WORKSPACE_GATE    → confirm org_idx / workspace_idx
Step 1-3. SCHEMA_FIRST          → confirm the events, dimensions, and metrics each content item needs
                                  (list_metrics → list_events/list_dimensions)
Step 1-4. DUPLICATE_GATE        → query that workspace's existing content and dashboards once with
                                  list_contents(company_cd, org_idx, workspace_idx)
Step 1-5. For a dashboard request, compare dashboard candidates in detail with get_dashboard before writing
          ├─ identical composition → have the user choose: use the existing one / create a copy / skip ⛔
          └─ partial overlap       → state the differences and let the user choose: add the missing content to the
                                     existing dashboard (update_dashboard) / create a new one / skip ⛔
```

**If the handed-over context has verified values, do not redo Steps 1-1 through 1-3.** `company_cd`, `project`,
`org_idx`, `workspace_idx`, and `metric_idx`/`event_idx`/`dimension_idx` are values design-dashboard confirmed against
the target company's schema, so use them as is — re-querying only repeats the same request and risks newly selecting a
different metric with a similar name.
By contrast, **always perform Steps 1-4 and 1-5 (DUPLICATE_GATE) even with a handed-over context** — the same content may have
been created between design time and save time, and design-dashboard cannot know the state just before the save.

Do **not call Step 1-4 once per content item** — fetch the workspace list once and compare it in Phase 2 against the names and
metrics of the content you decomposed (do not re-query the same organization repeatedly). However, if the response has
`truncated=true`, the list was cut off, so **do not use it as comparison evidence** — re-call it in Phase 2 per content item with
`name` (+ `metrics`).

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
Step 2-2. [DUPLICATE_GATE] Look for candidates with the same name or metric in the Step 1-4 list
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
  For event-based content, catching candidates by name and confirming with `get_content` is the only way.
- For period comparison, look first at `date_params`'s `start_date_type`/`end_date_type`.
  For `"V"` (relative), compare `start_value`/`end_value` — do not compare `start_date`/`end_date` here, because they are computed
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
Dashboard request                      → create_dashboard(contents=[the content_idx values confirmed in Phase 2, in display order])
                                          → return the dashboard url
```

**Do not compare dashboard duplicates by the `content_idx` set of their member content.** Recreating the same composition
also copies the child content, so every idx differs — compare by the `content_name` and `metrics` sets.
To add content to an existing dashboard, read it with `get_dashboard`, then pass the full new list to `update_dashboard`
after WRITE_APPROVAL, carrying over each existing item's `width`/`height`/`memo` so the current layout is kept.
Create a new dashboard only after showing the final composition and target workspace and obtaining WRITE_APPROVAL.

For a new layout the tool computes placement from the contents order, so **decide the order**. To keep an existing layout — a
template, a dashboard you are recreating, or any `update_dashboard` call — also pass each item's `width`/`height`/`memo`
(see [layout_policy.md](references/layout_policy.md)).

### Phase 4 — POST_WRITE_LINK

- Return the console link the tool returned: `url` from `create_*`/`create_dashboard`, `console_url` from `update_*`.

---

## Full Chain

```
[Decompose the request]
(PROJECT_ID_GATE) (ORG_WORKSPACE_GATE) (SCHEMA_FIRST) (DUPLICATE_GATE: check the dashboard first)
Per content item: preview_<type> → [duplicate check: get_content] → [WRITE_APPROVAL] → create_<type> → content_idx
  ├─ single & no dashboard needed → return the content url
  └─ dashboard request            → [duplicate check: get_dashboard] → create_dashboard → return the dashboard url
```

---

## Prohibited Behavior ❌

| Situation | Prohibited behavior | Correct behavior |
|------|----------|-----------|
| Before approval | Calling `create_*` right away | Verify with `preview_<type>`, then WRITE_APPROVAL |
| Duplicate unchecked | Saving without checking existing content | Find candidates with `list_contents` → confirm with `get_content` |
| Duplicate candidate found | Declaring "it already exists" from `match` alone | Compare in detail, then ask the user to reuse, copy, or skip |
| Metrics look empty | Concluding it is not a duplicate | It is event-based and so absent from the list — confirm with `get_content` |
| Dashboard duplicate | Comparing by the member `content_idx` set | Compare by the `content_name` and `metrics` sets (a copy has different idx values) |
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
| Too many `list_contents` candidates | Narrow with `workspace_idx`; if still too many, add `mine_only=true` or `content_type` |
| `list_contents` `truncated=true` | There are more candidates — do not conclude "no duplicate"; narrow the filters and query again |
| `create_*` failed | Check the server response in the error message → fix the parameters and retry. Stop if it is before dashboard assembly |
| Some content failed during dashboard assembly | Ask the user whether to proceed with only the successful `content_idx` values |
| Organization or workspace authorization error | Perform ORG_WORKSPACE_GATE again |
| MCP token or Hive session expired (`__AUTH_EXPIRED__`) | Explain that the user must sign in again. Cannot retry without user action |
