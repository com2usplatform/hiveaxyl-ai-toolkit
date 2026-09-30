# create_segment_snapshot (Extract a Segment Snapshot)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + **WRITE_APPROVAL** are required.

## When to Use

- To **freeze an existing segment again as of now**. The segment definition stays the same; only the target user set is rebuilt.
- When the existing snapshot is too old (`snapshot_age_days`) to use as is.
- When `create_segment` was saved with `set_base_snapshot=""` and therefore has no snapshot.

> A single segment accumulates **several** snapshots (for example, refreshed daily). Adding a snapshot does not remove the existing ones.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code |
| `org_idx` | Y | Organization idx. Used to verify access to the segment's project |
| `segment_idx` | Y | Segment idx. The return value of `create_segment` or the `segment_idx` from `list_segment_snapshots` |
| `title` | Y | Snapshot name. Because several accumulate under one segment, make it **convey the point in time** (for example, `"260730_China_Users"`) |

## Return Value

Returns the target segment and project, the snapshot title, the start status, the snapshot ID when available, and the console URL.

- `job_status` is always `"start"` — at the time of the return, extraction has only been started.
- `url` is the console link for POST_WRITE_LINK. If the response contains `snapshot_idx`, it is the snapshot detail
  link; otherwise it is the segment detail link.
  After extraction completes, provide the snapshot link from the `url` in `list_segment_snapshots`.
- `segment_title`/`appid_group` are the values the server looked up from `segment_idx`. Have the user confirm this is the intended segment.

## Decision Rules

- **Do not guess `segment_idx`** (NO_GUESSING). Always take it from an upstream tool's result.
  A single wrong digit can point at a different segment. The server also verifies company membership and the selected organization's access to the project.
- **It does not return the target user count.** Check the count with `list_segment_snapshots` once `job_status="complete"`.
- Completion takes time. If it does not appear on an immediate re-query, wait briefly and check once more before concluding —
  and do not call this tool again in the meantime, because each call creates another snapshot.

## On Failure

| Situation | Response |
|------|------|
| `ValidationError` (company mismatch) | The `segment_idx` belongs to a different company. Recheck with `list_segment_snapshots` |
| `ValidationError` (deleted segment) | A snapshot cannot be created for a deleted segment. Suggest creating a new one with `create_segment` |
| API error | Check the server response. Extraction did not start |

## Recommended Chain

```
list_segment_snapshots (confirm segment_idx) → [WRITE_APPROVAL] → create_segment_snapshot
→ list_segment_snapshots (confirm job_status completion and the user count)
```
