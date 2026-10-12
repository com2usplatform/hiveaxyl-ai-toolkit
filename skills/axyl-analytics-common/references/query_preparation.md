# Query Preparation

> **Prerequisite:** Read [`../SKILL.md`](../SKILL.md) and the required access/context references first.

### SCHEMA_FIRST

Before calling `preview_chart`:

1. `list_metrics(company_cd)` — check the metric list **first**.
   - If the desired metric is registered → use **metric mode**.
   - It is a revenue metric only when the dimension its `metric_config` aggregates has `is_price=1` in `list_dimensions` and
     its event also has an `is_currency=1` dimension — `SUM` alone
     does not mean revenue (play time or item quantity are sums too). For a revenue metric, verify the currency with
     `list_currencies(company_cd)` and pass `currency` as well. With no `is_currency=1` dimension, pass no `currency` and
     state that the amounts are not converted.
2. If the metric is not registered: call `list_events(company_cd)` → `list_dimensions(company_cd, event_name)` in order to verify the event and dimensions, then call in event mode.
3. Unless the user explicitly asks to register one, registering a metric is optional and never the first step. Query in
   event mode first, and propose `create_metric`
   only in the cases its tool specification lists under "When to Use" (reuse, a per-term period, a shared team definition,
   or an explicit request to register one), with WRITE_APPROVAL. Its tool specification is linked directly from `SKILL.md`.

Do not invent event names, property names, or metric names before verifying them.

Before calling `simulate_segment`/`create_segment`:

1. `list_segment_meta(company_cd, org_idx, appid_group)` — verify the available `property_category`/`property_name` values,
   selectable values (`value_type="enum"`), and whether period conditions are supported (`period_yn`).
2. Using a property name or value absent from the metadata in a condition is rejected before saving.
   Because an incorrect selectable value would create a **segment that matches no one without producing an error**,
   the server prevents this in advance.

### EXISTING_ASSET_FIRST

When the user asks for a metric or status value that a saved chart or dashboard could answer (for example, last week's
revenue). Breakdown analysis (`axyl-drill-down-metrics`) and anomaly detection (`axyl-detect-anomaly`) do not search on
their own; they match the company definition by using metric mode for registered metrics.

**Named asset in breakdown or anomaly analysis.** When the user names a saved chart or dashboard, read it (`get_content`, or
`get_dashboard` then `get_content`) and keep its metric, filters (query-wide and per-term), and project; if a setting cannot be
reproduced, say so. For a named dashboard, also apply its global filters (confirm each filter's dimension exists on the member's
event with `list_dimensions`) so the value matches the console, and say that they were applied. The console applies the member's
own filters and the global filters together (AND), so keep both, each with its own operator. When both are inclusion filters
on the same dimension, only the values in both lists remain (member `country` in {KR, US} with global {US} leaves US); when
the lists share no value (member {KR}, global {US}), both this query and the console return no data; when only some values
remain, say which. Other pairings (for example a `not_null` or exclusion filter) are applied as they are, and can also leave
nothing (member include {KR}, global exclude {KR}). Whatever the operators, when the result with both applied is empty, do
not report it as the metric's value (such as 0); tell the user the filters may conflict and show both. The calling skill decides the period. (This differs from
the lookup path in step 2, which states a dashboard's global settings instead of applying them.)

1. Search existing assets (charts and dashboards) first — `list_contents(company_cd, org_idx, name=keyword)`.
2. A candidate counts only after its project is confirmed with `get_content`; for a dashboard, call `get_dashboard` and
   check each member content with `get_content` (`get_dashboard` returns no project). For a content item, use its saved
   settings, replacing the saved period when the user explicitly requested another one. Before answering from it, compare
   its metrics, filters (query-wide and per-term), and breakdown dimensions with the request; show any filter or breakdown
   the user did not ask for with the answer, say the value reflects it, and offer to query again without it. When the chart
   breaks the metric down by a dimension the user did not ask for and they want one total, do not add up its rows for a
   distinct-user count or a ratio (users in several segments would be counted twice); query again with the chart's metric,
   filters, and period but without `dimensions`, and say so. For a dashboard, query the member
   content that answers the request with its own settings (and the user's requested period when given); do not merge the
   dashboard's global period or filters into it. When the dashboard has a global period or filters, show them with the
   answer, say that the value does not include them, and offer to query again with those settings as explicit conditions
   or with other criteria. Re-query only with conditions the user chooses; if the matching preview tool cannot take them
   (for example, `preview_funnel` has no `adhoc_filters`), say so. Convert a fixed global date to the member's preview format (`YYYY-MM-DD 00:00:00` with `F`; for a funnel member,
   `YYYY-MM-DD` with `ep`),
   and confirm each global filter's dimension exists on the member's event (`list_dimensions`) before re-querying. Give the saved asset's console link with the answer.
3. Only when none exists, run an ad hoc query with `preview_chart`.

This is the **read path**, where a roughly matching name is good enough to find a candidate (its filters and breakdowns are
still compared and stated as in step 2) — widen the keywords with
FUZZY_SEARCH_FALLBACK when the first search misses. Before **saving** new content the standard is the
opposite (a rough match must never be treated as a duplicate), so follow **DUPLICATE_GATE** instead.
Both start with the same `list_contents` call; only what you do with the candidates differs.

### FUZZY_SEARCH_FALLBACK

When an asset, event, or metric search fails:

1. First attempt: search with the keyword provided by the user.
2. Second attempt: search again with a shorter keyword or a synonym.
3. If the third attempt fails: present the full list and ask the user to choose.
4. If it is not in the list, explicitly state "Not found" and stop. Do not proceed with a nonexistent asset. On the
   EXISTING_ASSET_FIRST read path, go to its step 3 (ad hoc analysis) instead of stopping, and skip the full-list step.
