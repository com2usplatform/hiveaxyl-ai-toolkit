# list_user_groups (List User Groups)

Lists the user groups registered for a project. A user group is a set of users prepared in the
console, used to narrow the target of a user activity investigation.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- When the investigation target is not yet decided and candidates have to be picked from a condition
- To check whether a group already exists before creating one with `regist_user_group`

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `lang` | N | Label language. Default `ko` |

## Return Value

Returns `{"appid_group", "count", "groups"}`.
`groups` is `[{"idx", "type", "name", "segment_id", "segment_snapshot_id"}]`.

| `type` | Meaning |
|---|---|
| `builtin` | A default group provided by the Analytics system |
| `segment` | A group made from a segment. `segment_*` identifies the source |

Built-in group names state the condition directly.

```text
Top 100 users by revenue over the last 15 days
Top 100 users by cumulative revenue
Users whose last classification type is whale
Users new within the last 7 days
Users dormant for 3 days or more
```

## Decision Rules

- **Members are not included in this list.** Query them separately with `get_user_group`.
- `segment_id` and `segment_snapshot_id` appear only on `segment`-type groups. Use them to continue
  into segment tools such as `list_segment_snapshots`.
- The creator's internal account ID is not returned. If it is needed, check the console screen.
- When a built-in group matches the condition, prefer it over building a ranking with
  `preview_chart_rank` — the response is smaller and identifying evidence comes with the members.

## On Failure

- Organization or project access error: recheck the organization and project relationship.
- Empty result: no user groups are registered for this project.

## Recommended Chain

```text
list_user_groups → get_user_group → present candidates → check_user_exists → activity investigation
```
