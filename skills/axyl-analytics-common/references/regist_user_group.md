# regist_user_group (Create a User Group)

Creates a user group from a segment (or a segment snapshot). It lets user activity tracking narrow
its target to that set of users.

> **Prerequisite:** Follow WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When a segment condition is needed for an investigation but no `segment`-type group exists yet
- Always check with `list_user_groups` that no group for the same purpose exists before calling

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `game_name` | Y | Game name (`list_projects.game_name`). Never guessed |
| `name` | Y | Group name. Make it say what the group collects |
| `segment_id` | Y | Segment idx (`list_segment_snapshots.segment_idx`) |
| `segment_snapshot_id` | N | Snapshot idx (`list_segment_snapshots.snapshot_idx`). Omit to build from the segment alone |

## Return Value

Returns `{"group_id", "name", "appid_group", "console_url", "segment_id", "segment_snapshot_id",
"response"}`.

`console_url` is the link to the user activity tracking screen. **Include it when reporting the
write result** (POST_WRITE_LINK). It points at the project-level screen rather than a page for the
individual group, so also mention that the new group has to be found in the list there.
`group_id` is used afterwards by `get_user_group` and `check_user_exists(user_group_id=...)`.

## Decision Rules

- **Creation cannot be undone through MCP** — no group deletion tool is provided. Confirm the name
  with the user before calling.
- A group is not newly computed data; it is a named pointer to an existing segment. Even so, it stays
  in the console, so do not create one freely just to run a single investigation.
- **Reuse comes first.** Check `list_user_groups` and use an existing group when one fits.
- Creating a segment, extracting a snapshot, and then creating a group is a heavy flow. Propose it to
  the user and obtain approval before starting.

## On Failure

- Organization or project access error: recheck the organization and project relationship.
- API error: do not retry automatically. First check with `list_user_groups` whether the group was
  actually created — a retry can create two groups with the same name, and they cannot be deleted.

## Recommended Chain

```text
list_user_groups → no group for the same purpose
→ axyl-create-segment (segment + snapshot) → WRITE_APPROVAL → regist_user_group
→ get_user_group → present candidates
```
