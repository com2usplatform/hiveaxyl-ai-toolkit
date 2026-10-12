# Write Safety and Completion

> **Prerequisite:** Read [`../SKILL.md`](../SKILL.md) and the required access/context references first.

### DUPLICATE_GATE

Before calling `create_chart`/`create_chart_rank`/`create_funnel`/`create_retention`/`create_dashboard`:

```
Step 1. Query by the proposed name; for registered-metric-only content, also pass the metric measure names.
        Confirm the returned candidates in detail.
Step 2. No confirmed duplicate + any event-based measure, funnel, or retention
          → run one bounded widened query for the target workspace/content_type without name/metrics
            (once per target workspace and content type within the request; reuse it for other items of the same
            type, and rerun it after a workspace change or a failed or uncertain write)
          → inspect the returned rows (and returned dashboards for a dashboard containing such members)
          → if truncated, state how many same-type rows exist and that older rows were not checked;
            do not automatically expand with limit=0
Step 3. A candidate exists → compare full params with get_content (content). For a dashboard, call get_dashboard,
        then get_content for every content member (text and image panels excluded) and compare each member's full semantic composition as well as the
        dashboard-level date_params/adhoc_filters.
Step 4. Same content     → present the existing console URL and ask the user to choose reuse, create a copy,
                           or skip. Reuse is allowed only when target workspace access is confirmed.
        Different content → state in one line what differs (period, dimensions, filters, ...) and proceed
                            (a dashboard with partial overlap: offer add / copy / skip as in get_dashboard; offer add only when its permission is EDITOR).
```

- **Never answer "it already exists" from `match` alone.** `list_contents` only narrows candidates — the list
  response carries no `params` or `chart_type`. Confirm with the `params` from `get_content`/`get_dashboard`.
- **Do not conclude "not a duplicate" just because the metrics look different.** `metrics` carries only measures
  built from registered metrics — measures built from events, and the events of funnels and retentions, do not
  appear in the list, so it comes back `metrics_comparable=false` or holds only part of the real composition.
- Pass **only metric measure names** in `metrics`. Passing event names makes you miss candidates.
- For an event-based measure, funnel, or retention, inspect the bounded widened same-type result with `get_content`; for
  a dashboard containing any such member, inspect the returned widened dashboard candidates and then their members.
  When the list is truncated, say that older renamed copies were not exhaustively checked and include that limitation
  with WRITE_APPROVAL. Use `limit=0` only for an explicitly requested exhaustive audit or on an exact-name/type recovery
  query to resolve an uncertain prior write before retrying. Never use `mine_only` in DUPLICATE_GATE.
- **Recovery query** (after a failed or uncertain write): `list_contents(company_cd, org_idx, workspace_idx=<target>,
  content_type=<type>, name=<the name that was being saved>, limit=0)`. Count the write as done only when a row that was
  not among the candidates seen before the write matches the approved settings in `get_content`/`get_dashboard`; a
  same-name asset that existed before is not the new one.
- **Dashboard copy criteria.** Treat a dashboard as a copy only when its members match one-to-one and every matched
  member satisfies the full `get_content` duplicate criteria: `content_type`/`chart_type`, `project`, metric- and
  event-based measures, dimensions, filters (query-wide and per-term), and effective date settings. This comparison includes type-specific
  params such as ranking modes and limits, table display configuration, funnel `sections` and conversion settings,
  and retention `base_event`/`retention_event`/`identifier`/`display_format`. The dashboard-level
  `date_params` and `adhoc_filters` must match too. Names and `metrics` from `get_dashboard` narrow and pair candidates;
  they never prove a copy on their own. Do not compare by the member content idx set: recreating the same composition
  also copies the members, so every idx differs. This is the only place these criteria are defined; other skills follow it.
- This check is a read, so perform it without approval, and present the result when asking for WRITE_APPROVAL.
- If the user knows about the duplicate and still asks for a new one, create it. The gate **informs**; it does
  not block.
- This is the **write path**. EXISTING_ASSET_FIRST starts with the same `list_contents` call, but it serves an
  analysis request where a rough match suffices. Here a rough match must never be treated as a duplicate —
  do not carry FUZZY_SEARCH_FALLBACK's widen-and-accept behavior into this gate.

### WRITE_APPROVAL

For write operations such as creating or modifying metrics, defining segments, or changing dashboards:

- Explain the changes to the user before execution and obtain **explicit approval**.
- Do not execute write operations without approval.
- Calling a write again after a failure or rejection needs fresh approval, whether or not the input changed; say what
  changed or that nothing did. This covers every fix-and-call-again row in a tool reference's "On Failure" section.
- For content and dashboard saves, present the DUPLICATE_GATE result (whether one already exists and, if so, what differs) before obtaining approval.
- Segment write tools: `create_segment` (save definition), `create_segment_snapshot` (extract snapshot).
  **Obtain separate approval for each** — approval to save the segment does not also approve snapshot extraction.
  A snapshot is a BigQuery operation that means "freeze it at the current point in time," so ask separately.
  `simulate_segment` is a read, so it can be called without approval; use it as the **basis for obtaining approval**.
  `create_segment_from_classification` and `regist_user_group` are also writes, each with its own approval.
- Analytics configuration write tools: `regist_except_users`, `regist_start_dates`, `regist_metric_filter`, `regist_currency`.
  Show the current configuration, the project to change (the organization is used only for authorization), and the identifier
  or value, then obtain approval for each change. Several identifiers for the same tool may share one batch approval
  (still one call each).
  `regist_workspace`, `regist_org`, `regist_event`, `create_metric`, `regist_user_group`, and
  `create_segment_from_classification` create assets, and `regist_metric_filter` registrations cannot be edited; say that
  what they create cannot be deleted through MCP. Configuration
  approval does not count as approval to send a sample with `run_etl_simulation(org_idx, dry_run=false)`, and sample-send approval
  does not count as approval to change configuration.
- Several content items saved for the same request may share one batch approval when the summary lists each item with its
  DUPLICATE_GATE result.

### POST_WRITE_LINK

After a successful write:

- Return the console link the tool gave you with the result:
  - `url`: `create_chart`/`create_chart_rank`/`create_funnel`/`create_retention`, `create_dashboard`, `create_segment`,
    `create_segment_snapshot`, `create_segment_from_classification`
  - `console_url`: every `update_*`, `create_metric`, `regist_event`, `regist_event_dimension`, `regist_user_group`,
    `regist_workspace`, `request_workspace_permission`
- No link: `regist_except_users`, `regist_start_dates`, `regist_metric_filter`, `regist_currency`, and `regist_org` —
  point to the console settings screen.
- If the URL cannot be generated, state why.
- **Segments and snapshots are also write operations, so return links for them in the same way.** The tool provides the `url` field.

| Asset | Console URL |
|---|---|
| Content (chart, funnel, retention) | `url` returned by `create_*` (`console_url` from `update_*`) |
| Dashboard | `url` returned by `create_dashboard` (`console_url` from `update_dashboard`) |
| Segment | `url` returned by the tool |
| Snapshot | `url` returned by the tool |

- Do not assemble the URL yourself. Use the `url` returned by the tool exactly as given (the host can vary by environment).
- If the response has no `snapshot_idx`, `create_segment_snapshot` provides the segment detail link.
  After extraction completes, provide the snapshot link from the `url` returned by `list_segment_snapshots`.
