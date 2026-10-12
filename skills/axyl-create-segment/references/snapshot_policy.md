# Snapshot Policy (freshness, size, and reuse decisions)

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md).

## When to Use

- To decide whether to use an existing snapshot as is or take a new one.
- To verify that the target set is still valid before actually using a snapshot (for a send, targeting, and so on).

---

## The Relationship Between Segments and Snapshots

```
Segment (condition definition)          1
  └─ Snapshot (set fixed at a point)    N   ← refreshing daily accumulates one per day

Creating a segment without a snapshot leaves no target user set at all.
Taking a new snapshot does not remove the existing ones.
```

- **Segment = the conditions**, **snapshot = the user list frozen from those conditions at a specific point in time.** Do not confuse the two.
- With the default (`set_base_snapshot=""`), `create_segment` **saves only the definition.** Even right after creating a new
  segment, the snapshot is approved separately and created with `create_segment_snapshot`.
  (Passing `set_base_snapshot="set"` creates one base snapshot along with the save; in that case, avoid a duplicate call.)
- The `snapshots` array from `list_segment_snapshots` is in **most-recent-first** order.

## Judging Freshness

A snapshot is a set fixed at a past point in time. As time passes, these users get mixed in.

- Users who have already churned
- Users who have withdrawn
- Users who have opted out of notifications
- Users who no longer match the conditions (for example, a paying user who refunded, or a dormant user who came back)

```
Check snapshot_age_days
  ├─ today to a few days old   → a reuse candidate; show the elapsed days and let the user choose (as in Step 3 below)
  ├─ a week or more old        → state the elapsed days to the user and confirm whether to refresh
  └─ for a send + old          → refreshing with create_segment_snapshot is recommended
```

- **Do not use a snapshot without checking the elapsed days.** Tell the user how many days have passed.
- The acceptable age depends on the purpose. Present the elapsed days and hand the judgment to the user.

## Judging Size

```
Check snapshot_user_cnt
  ├─ 0 users              → no recipients. The conditions need redesigning
  ├─ a handful (ones–tens) → the conditions may be far too narrow. Confirm this is the intended size
  └─ large (tens of thousands+) → confirm the size suits the purpose. For a send, state the scope of impact
```

- The size can be known in advance with `simulate_segment`, before saving. Taking a snapshot just to find out is wasteful.
- An empty `snapshots` list means **no snapshot exists yet**. Right after an extraction request, re-check once before concluding;
  if none was requested, offer to extract one. Never re-call `create_segment_snapshot` while unsure.

## Reuse-First Principle

```
When a snapshot is needed:

Step 1. Check the existing snapshots with list_segment_snapshots
Step 2. Do the normalized raw conditions match the request? (summary is display-only; never judge from the name)
          └─ NO  → a new segment is needed (create_segment)
Step 3. Is the latest snapshot usable? (snapshot_age_days)
          ├─ YES → unless the user explicitly asked for a new one, show the elapsed days and let the user choose to
          │        reuse it or extract a new one
          └─ NO  → [WRITE_APPROVAL] → create_segment_snapshot
```

Do not take duplicate snapshots of the same conditions. Extraction is a BigQuery operation, which costs money and time.

## Waiting for Completion

```
Right after create_segment_snapshot (or create_segment with set_base_snapshot="set") returns
  (create_segment with the default set_base_snapshot="" makes no snapshot at all)
  → job_status = "start" (extraction has only been started; create_segment returns no job_status —
    check the base snapshot with list_segment_snapshots)
  → the target user count is unknown

list_segment_snapshots also returns in-progress snapshots along with their job_status
  → "start" means in progress; absent from the list immediately after a request may be a visibility delay
  → keep the request pending, advise querying again later, and never call create_segment_snapshot again while unsure
```

- Do not report a definite user count right after the return.
- Do not treat it as a failure just because it is not visible on an immediate re-query. Advise querying again shortly.

---

## Cautions When Interpreting Conditions

- **Do not judge the target from the segment's name or description.** In real data, careless names are common.
- Judge identity from the normalized raw condition structure. Use `conditions[].summary` (for example,
  `"User info · Language: Simplified Chinese"`) only to explain the target to the user.
- With `with_labels=True` (the default), the labels are filled in. Missing labels mean the property metadata query failed, so
  interpret them yourself with `list_segment_meta` or explain using the raw values.
- Only condition-based (`created_way="standard"`) segments are returned. Segments created by CSV upload or a direct query have no
  extraction conditions and do not appear in the list — because the target cannot be verified.

## On Failure

| Situation | Response |
|------|------|
| `snapshots` is an empty list | If no extraction was requested, offer to extract. After a request, treat the empty list as pending visibility and query again later; do not call it failed or offer a retry until the service or an operator confirms that the accepted request can no longer create a snapshot (ask the user to confirm with the Analytics operator — no tool reports it). A retry requires fresh WRITE_APPROVAL |
| `job_status="start"` | In progress. Advise querying again shortly. Do not re-extract. Do not report a count |
| `segment_idx` company mismatch | It is another company's segment. Reconfirm with `list_segment_snapshots` |
| Deleted segment | A snapshot cannot be created. Propose creating a new one with `create_segment` |
| The snapshot never completes | Report it as pending and ask the user to confirm with the Analytics operator — no tool reports it. Propose simplifying the conditions or period, but retry only after confirmation that the previous request can no longer create a snapshot and after fresh WRITE_APPROVAL |
