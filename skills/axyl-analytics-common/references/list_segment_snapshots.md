# list_segment_snapshots (List Segments and Snapshots)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE is required.

## When to Use

- When you need to choose an existing segment. This is the only query path that yields `segment_idx`/`snapshot_idx`.
- To confirm **whether a snapshot completed and how many users it targets** after `create_segment`/`create_segment_snapshot`.
- To verify a snapshot's **freshness, size, and conditions** before actually using it (for a send, and so on).

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code |
| `org_idx` | Y | Organization idx. Used to verify access to the target project |
| `appid_group` | Y | Project ID (the `appid_group` from `list_projects`) |
| `with_labels` | N | `true` (default) fills in labels and summaries for the conditions |
| `lang` | N | Label language (default `"ko"`) |

## Return Value

Returns results grouped by segment. Each segment includes the project, the name and description, a condition summary,
the console URL, and its snapshot list. Each snapshot includes the status, creation time, elapsed days, target user count, and URL.

## Decision Rules

- **Do not judge the target from the segment name.** Names and descriptions are often written carelessly.
  Base the judgment on `conditions[].summary` (the actual extraction conditions).
- **Always check `snapshot_age_days`.** A snapshot is a set fixed at a past point in time, so an old one will include users
  who have since churned, withdrawn, or opted out. Do not use an old snapshot as is — propose refreshing it with `create_segment_snapshot`.
- **Distinguish states by `job_status`.** Only `"complete"` is usable; `"start"` means extraction is still running, so
  `snapshot_table_name`/`snapshot_user_cnt` are still empty (do not report a user count).
- An empty `snapshots` list means **no visible snapshot exists yet**. If `create_segment_snapshot` was just called, the row
  may be delayed: wait briefly and query once more, then leave the request pending if it is still absent. **Never call
  `create_segment_snapshot` again while unsure** (each call creates another snapshot). If none was requested, report
  "no snapshot yet" and offer to extract one. Call a request failed only when the service or an operator confirms that
  the accepted request can no longer create a snapshot, and obtain fresh WRITE_APPROVAL before retrying.
- When a segment has several snapshots, they are in **most-recent-first** order. Absent a specific reason, use the latest one.
- When telling the user about a segment or snapshot, include the `url` (console link). Do not assemble it yourself.
- Only condition-based (`created_way="standard"`) segments are returned. Segments created by CSV upload or a direct query are not in the list —
  their extraction conditions are not in the database, so the target cannot be verified.

## On Failure

- Empty result: the project has no condition-based segments. Propose creating one with `create_segment`.
- The segment exists but `snapshots` is empty: if none was requested, propose extracting one. Right after an extraction
  request, re-check once and then leave it pending if still absent; do not call `create_segment_snapshot` again while unsure.
- `conditions` has no labels (`summary` and so on): only the property metadata query failed. The raw condition values are still valid, so
  interpret them yourself with `list_segment_meta` if needed.

## Recommended Chain

```
(PROJECT_ID_GATE) → list_segment_snapshots
  ├─ a usable snapshot exists → use it as is
  └─ none or too old → [WRITE_APPROVAL] → create_segment_snapshot → query again
```
