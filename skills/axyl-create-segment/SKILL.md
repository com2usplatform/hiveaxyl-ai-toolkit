---
name: axyl-create-segment
metadata:
  version: "1.0.0"
description: |
  Turns a natural-language request into segment conditions, simulates the estimated user count, saves the segment, and
  extracts a snapshot (a user set fixed at a point in time). Adding a snapshot to an existing segment is also this
  skill's job.

  TRIGGER when:
  - The user asks to create a segment (for example, "create a segment of paying iOS users")
  - The user asks how many users meet certain conditions (simulation only, no save)
  - The user asks to take or refresh a snapshot of an existing segment
  - The user asks what segments and snapshots exist

  DO NOT TRIGGER when:
  - The request is to view a metric split by dimension (OS, country, market) or a user ranking → axyl-drill-down-metrics
  - The request is to create chart, funnel, retention, or dashboard content → axyl-create-content
  - The request is only to send a push → currently unsupported
    (this skill stops at segments and snapshots; if segment creation is also requested, complete only that part)
  - The request is development work unrelated to analytics
---

# axyl-create-segment

> **CRITICAL — Always review the common rules in [axyl-analytics-common](../axyl-analytics-common/SKILL.md) first.**
> **CRITICAL — `create_segment` and `create_segment_snapshot` are write operations. Never run them without WRITE_APPROVAL.**
> **CRITICAL — Always show the estimated user count with `simulate_segment` before saving. Do not ask for approval without showing the count.**
> **CRITICAL — Use only `list_segment_meta` results for condition property names and values (NO_GUESSING). A wrong value produces a segment matching no one, without any error.**
> **CRITICAL — Take `segment_idx` and `snapshot_idx` only from upstream tool results. Do not guess them.**
> **CRITICAL — Show the user only the condition summary (`summary`). Do not expose internal code values such as `value_range_type`, `date_type`, or `start_value` (the display rules in axyl-analytics-common).**

---

## Tools

- **Schema (read):** `list_segment_meta`
  → [list_segment_meta.md](../axyl-analytics-common/references/list_segment_meta.md)
- **Verification (read):** `simulate_segment`
  → [simulate_segment.md](../axyl-analytics-common/references/simulate_segment.md)
- **Save (write):** `create_segment`
  → [create_segment.md](../axyl-analytics-common/references/create_segment.md)
- **Snapshot (write):** `create_segment_snapshot`
  → [create_segment_snapshot.md](../axyl-analytics-common/references/create_segment_snapshot.md)
- **Query (read):** `list_segment_snapshots`
  → [list_segment_snapshots.md](../axyl-analytics-common/references/list_segment_snapshots.md)

Segment tools need `org_idx` to verify access to the target project, but because segments are not workspace assets,
`workspace_idx` is not needed. Follow Step 1-1: confirm `org_idx` with `list_organizations(company_cd)` (add `appid_group` only when the project is already known), then take
`appid_group` and `game_name` from the **same row** of `list_projects(company_cd, org_idx)`.

## Reference Documents

- [Condition design patterns](references/condition_patterns.md) — examples of decomposing a natural-language request into `property_groups`
- [Snapshot policy](references/snapshot_policy.md) — criteria for judging freshness and size, and the segment-to-snapshot 1:N structure

---

## Workflow

### Prerequisite — Review the common rules

PROJECT_ID_GATE, SCHEMA_FIRST, WRITE_APPROVAL, and NO_GUESSING from axyl-analytics-common apply.
Workspace selection does not apply, but pass every segment tool an `org_idx` whose access to the target project has been verified.

### Phase 0 — Classify the request

```
Split the request three ways.

A. Create a segment from new conditions  → Phase 1 → 2 → 3 → 5
B. Only want the user count (no save)    → Phase 1 → 2, then stop
C. Take a snapshot of an existing segment → Phase 1 → 4 → 5
```

If the conditions are unclear, ask the user here. Do not proceed on a guess.
For decomposition examples, see [references/condition_patterns.md](references/condition_patterns.md).

### Phase 1 — Gates and schema (axyl-analytics-common)

```
Step 1-1. PROJECT_ID_GATE       → confirm company_cd, then org_idx and appid_group / game_name
                                  → list_organizations(company_cd), adding appid_group only when the project is already known:
                                    one candidate → use it;
                                    several → show them all and wait for the user's choice ⛔
                                  → list_projects(company_cd, org_idx): take appid_group and game_name
                                    from the same row
Step 1-2. SCHEMA_FIRST          → list_segment_meta(company_cd, org_idx, appid_group)
                                  → the usable property_category / property_name
                                  → value_type (enum: a list of selectable values / range: a range input)
                                  → period_yn (only Y properties can carry a period condition)
```

If the property you want is not in the metadata, that condition cannot be built. Propose an alternative property or stop.

### Phase 2 — Simulation (required before saving)

```
Step 2-1. Convert the request into property_groups (using only property_names and values from the metadata)
Step 2-2. Call simulate_segment — exactly once, with the conditions the user stated ⛔
Step 2-3. Present the result to the user and stop
            - estimated count / total count / proportion (%)
            - conditions (the condition summary that will be saved)
            - condition_details (which condition narrowed the scope)
Step 2-4. If the count is zero, or looks too small or too large for the purpose
            → **only propose** adjustments and wait for the user to choose ⛔
            → if the user chooses an adjustment, call Step 2-2 again with those conditions (once)
```

> **Do not arbitrarily change the conditions and re-simulate.** Adjusting a threshold or period yourself because the count
> seems low or high produces a different segment from the one the user asked for. Show the result as is
> and ask "Would you like to adjust the conditions?" — the judgment is the user's.
>
> `user_proportion` is expressed in **percent (%)**. `0.0004` is 0.0004%, not 0.04%.
> If the request is B (check the count), stop here — do not save.

**Proposal format** (do not act on it; get a choice)

```
The current conditions match N users. (X% of M total)
Which condition narrowed it: <grounded in condition_details>

Shall we proceed as is, or adjust the conditions?
  A. Save as is
  B. Relax the threshold (for example, at least 10 → at least 1)
  C. Widen the period (for example, today → the last 7 days)
  D. Remove a condition (for example, drop the OS condition)
```

- Ground each proposed adjustment in the condition that **actually narrowed the scope** in `condition_details`. Do not build it on a hunch.
- If the count is excessive, propose the opposite — adding conditions or shortening the period.
- Do not set thresholds yourself. Whether "N users is too few" depends on the purpose, so present the figure and leave the judgment.

### Phase 3 — Save the segment (definition only)

```
Step 3-1. [WRITE_APPROVAL] Wait for explicit approval to save ⛔
            (ask only after presenting the count and conditions from Phase 2)
Step 3-2. Call create_segment → collect segment_idx
            - title: a name that reveals the conditions (for example, "iOS Chinese-language paying users")
            - use the default ("") for set_base_snapshot → saves the definition only, creates no snapshot
Step 3-3. Show the user the returned conditions (summary sentence) and url (console link)
            → POST_WRITE_LINK: use the url the tool gave, exactly as given (never assemble it yourself)
```

> A segment is only a **condition definition**. Up to this step, no target user set exists.
> **Ask separately** whether to go on to Phase 4 and take a snapshot.

### Phase 4 — Extract a snapshot (same for new and existing)

```
Step 4-1. For an existing segment, call list_segment_snapshots(company_cd, org_idx, appid_group)
            → identify which segment it is from conditions[].summary (never judge from the name)
            → check the existing snapshots' job_status / snapshot_age_days / snapshot_user_cnt
            → if a usable recent snapshot already exists, use it and stop (no unnecessary extraction)
Step 4-2. [WRITE_APPROVAL] Wait for explicit approval: "Shall we create a snapshot as of now?" ⛔
            - explain that a snapshot freezes the users who currently match these conditions
            - even a segment just created in Phase 3 is asked again here, with no exception
Step 4-3. create_segment_snapshot(company_cd, org_idx, segment_idx, title)
            - title: make the point in time clear (for example, "260730_logged_in_today")
```

For the judgment criteria, see [references/snapshot_policy.md](references/snapshot_policy.md).
If the user does not want a snapshot, leave the segment definition and stop — Phase 4 alone can be redone later.

### Phase 5 — Confirm completion

```
Check that snapshot's job_status with list_segment_snapshots.
  ├─ "complete" → return snapshot_idx / snapshot_user_cnt to the user
  ├─ "start"    → extraction is in progress. Advise querying again shortly (do not re-extract)
  └─ not in the list → right after the call, wait briefly and check once more (do not call create again);
                       still absent → leave it pending and advise checking again later; retry only after
                       service/operator confirmation and a fresh WRITE_APPROVAL
```

- **POST_WRITE_LINK**: the tools return a `url` for both segments and snapshots. Include the link when reporting completion.
  Right after `create_segment_snapshot` there may be no `snapshot_idx`, so the segment link may come back;
  once extraction finishes, provide the snapshot `url` from `list_segment_snapshots`.
- A snapshot does not complete immediately. Do not state a user count right after the return.
- With `job_status="start"`, `snapshot_table_name`/`snapshot_user_cnt` are still empty. Do not report a user count.

---

## Full Chain

```
[Classify the request]
(PROJECT_ID_GATE) → list_segment_meta (SCHEMA_FIRST)
  │
  ├─ A. New segment
  │     simulate_segment (once) → [present the count · confirm whether to adjust] ⟲ re-call only if the user chooses
  │     → [WRITE_APPROVAL: save] → create_segment (definition only)
  │     → [WRITE_APPROVAL: snapshot] → create_segment_snapshot
  │     → list_segment_snapshots (check job_status)
  │
  ├─ B. Count only
  │     simulate_segment → present the result and stop (no saving)
  │
  └─ C. Snapshot of an existing segment
        list_segment_snapshots (check conditions and freshness) → [WRITE_APPROVAL: snapshot]
        → create_segment_snapshot → list_segment_snapshots (check job_status)
```

---

## Prohibited Behavior ❌

| Situation | Prohibited behavior | Correct behavior |
|------|----------|-----------|
| Before saving | Calling `create_segment` without a simulation | Check the count with `simulate_segment` → WRITE_APPROVAL |
| Property name or value unclear | Writing the condition on a guess | Confirm with `list_segment_meta` and use only the returned values |
| Estimated count is zero | Saving anyway | Stop the save. Point to the bottleneck condition via `condition_details` and propose a redesign |
| Count is low or high | Arbitrarily changing conditions and re-simulating | Present the result and get a choice: "Would you like to adjust the conditions?" |
| Adjusting conditions | Changing a threshold or period without user confirmation | Present the change, get approval, then re-call once with those conditions |
| Displaying a proportion | Converting `0.0004` to "0.04%" | Write the value as `%` as given (0.0004%) |
| Choosing a segment | Judging the target from the name and description alone | Judge from `conditions[].summary` (the actual conditions) |
| `segment_idx` | Guessing or inventing it | Use the `create_segment` return value or a `list_segment_snapshots` result |
| Old snapshot | Using it without checking the elapsed days | Check `snapshot_age_days` and propose a refresh if needed |
| Right after a snapshot | Reporting a definite user count | Report the count after confirming `job_status='complete'` |
| Unconfirmed snapshot | Passing "in progress" off when it is not in the list, declaring failure from an immediate empty result, or re-extracting because it is not visible yet | Report whether it is `job_status='start'` or absent; after a request, re-check once and leave an absent result pending. Retry only after service/operator confirmation that the previous request cannot create a snapshot, plus fresh WRITE_APPROVAL |
| After saving a segment | Extracting a snapshot too, without approval | Get separate approval for the snapshot in Phase 4 |
| User-facing display | Exposing raw values such as `value_range_type` or `start_value` | Display the condition summary (`summary`) sentence |
| After saving or extracting | Reporting only `segment_idx` with no link | Return the `url` the tool gave alongside (POST_WRITE_LINK) |
| Links | Assembling the URL yourself | Use the tool's returned `url` as is |
| Saving tokens | Using `with_labels=false` for a user-facing query | Keep `with_labels` at its default (true) — turning it off leaves labels and summaries empty, with only raw values |
| Period condition | Specifying `date_type` on a `period_yn="N"` property | Check `period_yn` in the metadata and remove the period condition |

---

## Exception Handling

| Situation | Response |
|------|------|
| The property you want is not in the metadata | Propose an alternative property, or explain that "a segment cannot be built with that condition" and stop |
| `ValidationError` (property name or value) | Choose from the available list in the message and retry. Do not edit arbitrarily |
| `ValidationError` (period condition) | It is a `period_yn="N"` property. Clear `date_type` and retry |
| Simulated count is zero | Do not save. **Propose** relaxing conditions or widening the period **and get a choice** (do not re-call arbitrarily) |
| Simulated count is excessive | State the size and **propose** adding conditions or shortening the period. Do not change conditions without approval |
| `condition_details` is an empty list | Only the detail query failed. The estimated count is still valid, so proceed with it |
| `snapshots` is an empty list | No snapshot yet. Right after an extraction request, re-check once before concluding; if none was requested, offer to extract. Never re-call `create_segment_snapshot` while unsure |
| `job_status="start"` | Extraction is in progress. Advise querying again shortly. Do not report a count or re-extract |
| No condition labels | The property metadata query failed. Explain with the raw condition values, or interpret them yourself with `list_segment_meta` |
| `segment_idx` company mismatch | It is another company's segment. Reconfirm with `list_segment_snapshots` |
| Deleted segment | A snapshot cannot be created. Propose creating a new one with `create_segment` |
| Not connected to the Hive Axyl MCP server (first install, never signed in), or the MCP token or Hive session expired (`__AUTH_EXPIRED__`) | Apply MCP_CONNECTION_GATE in axyl-analytics-common. Cannot retry without user action |
